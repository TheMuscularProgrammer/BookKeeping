import json
import os
from datetime import datetime
from kafka import KafkaConsumer
from sqlalchemy import create_engine, text
from contextlib import contextmanager
import redis
import requests
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:example@localhost:5432/mydatabase')
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://localhost:5004')

# Database setup
engine = create_engine(DATABASE_URL)

# Redis Client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@contextmanager
def get_db_connection():
    connection = engine.connect()
    transaction = connection.begin()
    try:
        yield connection
        transaction.commit()
    except Exception as e:
        transaction.rollback()
        raise
    finally:
        connection.close()

def send_notification(user_email, transaction_type, amount, account_number, to_account_number=None):
    """שליחת התראה דרך notification service"""
    try:
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications/transaction",
            json={
                'type': transaction_type,
                'amount': amount,
                'user_email': user_email,
                'account_number': account_number,
                'to_account_number': to_account_number
            },
            timeout=5
        )
        logger.info(f"Notification sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

def process_transfer_request(message):
    """עיבוד בקשת העברה מ-Kafka"""
    transfer_request_id = message['transfer_request_id']
    from_account_id = message['from_account_id']
    to_account_id = message['to_account_id']
    amount = message['amount']
    state = message['state']
    requires_approval = message['requires_approval']
    
    logger.info(f"🔄 Processing transfer {transfer_request_id}: state={state}, amount=${amount/100:.2f}, requires_approval={requires_approval}")
    
    # אם דורש אישור ועדיין pending - ממתין
    if requires_approval and state == 'pending':
        logger.info(f"⏳ Transfer {transfer_request_id} requires approval. Waiting...")
        return
    
    # אם approved - מבצעים את ההעברה!
    if state == 'approved':
        try:
            with get_db_connection() as connection:
                # בדיקה אם כבר עובד
                transfer = connection.execute(
                    text('SELECT * FROM transfer_requests WHERE id = :id'),
                    {'id': transfer_request_id}
                ).fetchone()
                
                if not transfer:
                    logger.error(f"❌ Transfer request {transfer_request_id} not found in database")
                    return
                
                if transfer.state == 'completed':
                    logger.info(f"✅ Transfer {transfer_request_id} already completed")
                    return
                
                # קבלת פרטי חשבונות
                from_account = connection.execute(
                    text('SELECT * FROM accounts WHERE id = :id'),
                    {'id': from_account_id}
                ).fetchone()
                
                to_account = connection.execute(
                    text('SELECT * FROM accounts WHERE id = :id'),
                    {'id': to_account_id}
                ).fetchone()
                
                # בדיקת יתרה (שוב, למקרה ששינו)
                if from_account.balance_cents < amount:
                    logger.error(f"❌ Insufficient funds for transfer {transfer_request_id}")
                    # עדכון ל-failed
                    connection.execute(
                        text("""
                            UPDATE transfer_requests 
                            SET state = 'failed', decline_reason = 'Insufficient funds', updated_at = :updated_at 
                            WHERE id = :id
                        """),
                        {'id': transfer_request_id, 'updated_at': datetime.now()}
                    )
                    redis_client.hset(f"transfer:{transfer_request_id}", 'state', 'failed')
                    return
                
                # 💰 ביצוע ההעברה!
                logger.info(f"💰 Executing transfer: ${amount/100:.2f} from {from_account.account_number} to {to_account.account_number}")
                
                # 1. ניכוי מחשבון המקור
                connection.execute(
                    text('UPDATE accounts SET balance_cents = balance_cents - :amount, updated_at = :updated_at WHERE id = :id'),
                    {'amount': amount, 'id': from_account_id, 'updated_at': datetime.now()}
                )
                
                # 2. הוספה לחשבון היעד
                connection.execute(
                    text('UPDATE accounts SET balance_cents = balance_cents + :amount, updated_at = :updated_at WHERE id = :id'),
                    {'amount': amount, 'id': to_account_id, 'updated_at': datetime.now()}
                )
                
                # 3. יצירת רשומת transaction
                import uuid
                transaction_id = str(uuid.uuid4())
                connection.execute(
                    text("""
                        INSERT INTO transactions 
                        (id, initiator_id, from_bank_account_id, to_bank_account_id, amount, created_at, updated_at)
                        VALUES (:id, :initiator_id, :from_account_id, :to_account_id, :amount, :created_at, :updated_at)
                    """),
                    {
                        'id': transaction_id,
                        'initiator_id': transfer.initiator_id,
                        'from_account_id': from_account_id,
                        'to_account_id': to_account_id,
                        'amount': amount,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                )
                
                # 4. עדכון transfer_request ל-completed
                connection.execute(
                    text("""
                        UPDATE transfer_requests 
                        SET state = 'completed', transaction_id = :transaction_id, updated_at = :updated_at 
                        WHERE id = :id
                    """),
                    {'id': transfer_request_id, 'transaction_id': transaction_id, 'updated_at': datetime.now()}
                )
                
                # 5. עדכון Redis
                redis_client.hset(f"transfer:{transfer_request_id}", 'state', 'completed')
                redis_client.hset(f"transfer:{transfer_request_id}", 'transaction_id', transaction_id)
                
                logger.info(f"✅ Transfer {transfer_request_id} completed successfully! Transaction ID: {transaction_id}")
                
                # 6. שליחת התראה
                user = connection.execute(
                    text('SELECT email FROM users WHERE id = :id'),
                    {'id': transfer.initiator_id}
                ).fetchone()
                
                if user:
                    send_notification(
                        user.email,
                        'transfer',
                        amount,
                        from_account.account_number,
                        to_account.account_number
                    )
                
        except Exception as e:
            logger.error(f"❌ Error processing transfer {transfer_request_id}: {e}")
            # עדכון ל-failed
            try:
                with get_db_connection() as connection:
                    connection.execute(
                        text("""
                            UPDATE transfer_requests 
                            SET state = 'failed', decline_reason = :reason, updated_at = :updated_at 
                            WHERE id = :id
                        """),
                        {'id': transfer_request_id, 'reason': str(e), 'updated_at': datetime.now()}
                    )
                    redis_client.hset(f"transfer:{transfer_request_id}", 'state', 'failed')
            except Exception as db_error:
                logger.error(f"Failed to update transfer state: {db_error}")

def process_approval(message):
    """עיבוד אישור - מעבד מחדש את ההעברה"""
    transfer_request_id = message['transfer_request_id']
    
    logger.info(f"✅ Processing approval for transfer {transfer_request_id}")
    
    # קבלת הפרטים המלאים מה-DB
    with get_db_connection() as connection:
        transfer = connection.execute(
            text('SELECT * FROM transfer_requests WHERE id = :id'),
            {'id': transfer_request_id}
        ).fetchone()
        
        if not transfer:
            logger.error(f"Transfer request {transfer_request_id} not found")
            return
        
        # יצירת הודעה לעיבוד
        transfer_message = {
            'transfer_request_id': str(transfer.id),
            'from_account_id': str(transfer.from_account_id),
            'to_account_id': str(transfer.to_account_id),
            'amount': transfer.amount,
            'state': 'approved',
            'requires_approval': transfer.requires_approval
        }
        
        # עיבוד ההעברה
        process_transfer_request(transfer_message)

def main():
    """פונקציה ראשית - צריכת הודעות מ-Kafka"""
    logger.info("🚀 Starting Transfer Processor...")
    
    # המתנה ל-Kafka
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # ניסיון חיבור
            test_consumer = KafkaConsumer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                consumer_timeout_ms=1000
            )
            test_consumer.close()
            logger.info("✅ Successfully connected to Kafka")
            break
        except Exception as e:
            retry_count += 1
            logger.warning(f"⏳ Waiting for Kafka... (attempt {retry_count}/{max_retries})")
            time.sleep(2)
    
    if retry_count >= max_retries:
        logger.error("❌ Failed to connect to Kafka after maximum retries")
        return
    
    # יצירת consumers
    transfer_consumer = KafkaConsumer(
        'transfer-requests',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='transfer-processor-group',
        auto_offset_reset='earliest'
    )
    
    approval_consumer = KafkaConsumer(
        'transfer-approvals',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='transfer-processor-group',
        auto_offset_reset='earliest'
    )
    
    decline_consumer = KafkaConsumer(
        'transfer-declines',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='transfer-processor-group',
        auto_offset_reset='earliest'
    )
    
    logger.info("👂 Listening for transfer requests, approvals, and declines...")
    
    try:
        while True:
            # עיבוד transfer requests
            for message in transfer_consumer:
                try:
                    logger.info(f"📨 Received transfer request: {message.value.get('transfer_request_id')}")
                    process_transfer_request(message.value)
                except Exception as e:
                    logger.error(f"Error processing transfer request: {e}")
            
            # עיבוד approvals
            for message in approval_consumer:
                try:
                    logger.info(f"✅ Received approval: {message.value.get('transfer_request_id')}")
                    process_approval(message.value)
                except Exception as e:
                    logger.error(f"Error processing approval: {e}")
            
            # עיבוד declines (רק לוג)
            for message in decline_consumer:
                try:
                    transfer_id = message.value['transfer_request_id']
                    reason = message.value.get('decline_reason', 'No reason provided')
                    logger.info(f"❌ Transfer {transfer_id} declined: {reason}")
                except Exception as e:
                    logger.error(f"Error processing decline: {e}")
            
            time.sleep(0.1)  # מניעת busy waiting
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Transfer Processor...")
    finally:
        transfer_consumer.close()
        approval_consumer.close()
        decline_consumer.close()

if __name__ == '__main__':
    main()