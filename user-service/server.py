import grpc
from concurrent import futures
import bcrypt
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from contextlib import contextmanager
import os
import jwt

# Import generated gRPC code (נייצר אותו בשלב הבא)
import user_service_pb2
import user_service_pb2_grpc

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:example@localhost:5432/mydatabase')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')

# Database setup
engine = create_engine(DATABASE_URL)

@contextmanager
def get_db_connection():
    connection = engine.connect()
    try:
        yield connection
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise
    finally:
        connection.close()

class UserService(user_service_pb2_grpc.UserServiceServicer):
    
    def CreateUser(self, request, context):
        """Create a new user"""
        try:
            # Hash password
            hashed_password = bcrypt.hashpw(
                request.password.encode('utf-8'), 
                bcrypt.gensalt()
            )
            
            with get_db_connection() as connection:
                # Check if user exists
                existing_user = connection.execute(
                    text("SELECT * FROM users WHERE email = :email"),
                    {'email': request.email}
                ).fetchone()
                
                if existing_user:
                    context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                    context.set_details('Email already exists')
                    return user_service_pb2.CreateUserResponse()
                
                # Create user
                user_id = str(uuid.uuid4())
                connection.execute(
                    text(
                        "INSERT INTO users (id, first_name, last_name, email, password, created_at, updated_at) "
                        "VALUES (:user_id, :first_name, :last_name, :email, :password, :created_at, :updated_at)"
                    ),
                    {
                        'user_id': user_id,
                        'first_name': request.first_name,
                        'last_name': request.last_name,
                        'email': request.email,
                        'password': hashed_password.decode('utf-8'),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                )
                
                return user_service_pb2.CreateUserResponse(
                    id=user_id,
                    message="User created successfully"
                )
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_service_pb2.CreateUserResponse()
    
    def ListUsers(self, request, context):
        """List all users with pagination"""
        try:
            page = request.page if request.page > 0 else 1
            page_size = request.page_size if request.page_size > 0 else 10
            offset = (page - 1) * page_size
            
            with get_db_connection() as connection:
                # Get total count
                total = connection.execute(
                    text("SELECT COUNT(*) FROM users")
                ).scalar()
                
                # Get users
                users = connection.execute(
                    text("SELECT id, first_name, last_name, email, created_at FROM users LIMIT :limit OFFSET :offset"),
                    {'limit': page_size, 'offset': offset}
                ).fetchall()
                
                user_list = [
                    user_service_pb2.User(
                        id=str(user.id),
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                        created_at=user.created_at.isoformat()
                    )
                    for user in users
                ]
                
                return user_service_pb2.ListUsersResponse(
                    users=user_list,
                    total=total
                )
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_service_pb2.ListUsersResponse()
    
    def Login(self, request, context):
        """Authenticate user and return JWT token"""
        try:
            with get_db_connection() as connection:
                user = connection.execute(
                    text("SELECT * FROM users WHERE email = :email"),
                    {'email': request.email}
                ).fetchone()
                
                if not user or not bcrypt.checkpw(
                    request.password.encode('utf-8'),
                    user.password.encode('utf-8')
                ):
                    context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                    context.set_details('Invalid credentials')
                    return user_service_pb2.LoginResponse()
                
                # Create JWT token
                token = jwt.encode(
                    {
                        'user_id': str(user.id),
                        'email': user.email,
                        'exp': datetime.utcnow() + timedelta(hours=24)
                    },
                    JWT_SECRET_KEY,
                    algorithm='HS256'
                )
                
                return user_service_pb2.LoginResponse(
                    access_token=token,
                    user_id=str(user.id),
                    message="Login successful"
                )
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_service_pb2.LoginResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:5001')
    print("User Service (gRPC) starting on port 5001...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()