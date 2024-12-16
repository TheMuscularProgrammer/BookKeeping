-- Generated from: https://drawsql.app/teams/get-shit-done/diagrams/oribookkeeping
-- How to connect: PGPASSWORD='example' psql -U postgres -h localhost -d mydatabase

CREATE TABLE IF NOT EXISTS "accounts"(
    "id" UUID NOT NULL,
    "owner_id" UUID NOT NULL,
    "account_number" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "balance_cents" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS "accounts_account_number_index" ON "accounts"("account_number");
ALTER TABLE "accounts" ADD PRIMARY KEY("id");
ALTER TABLE "accounts" ADD CONSTRAINT "accounts_owner_id_foreign" FOREIGN KEY("owner_id") REFERENCES "users"("id");

CREATE TABLE IF NOT EXISTS "users"(
    "id" UUID NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS "users_email_index" ON "users"("email");
ALTER TABLE "users" ADD PRIMARY KEY("id");
ALTER TABLE "users" ADD CONSTRAINT "users_email_unique" UNIQUE("email");

CREATE TABLE IF NOT EXISTS "transactions"(
    "id" UUID NOT NULL,
    "initiator_id" UUID NOT NULL,
    "from_bank_account_id" UUID NULL,
    "to_bank_account_id" UUID NULL,
    "amount" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS "transactions_from_bank_account_id_index" ON "transactions"("from_bank_account_id");
CREATE INDEX IF NOT EXISTS "transactions_to_bank_account_id_index" ON "transactions"("to_bank_account_id");
ALTER TABLE "transactions" ADD PRIMARY KEY("id");

ALTER TABLE "transactions" ADD CONSTRAINT "transactions_to_bank_account_id_foreign" FOREIGN KEY("to_bank_account_id") REFERENCES "accounts"("id");
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_from_bank_account_id_foreign" FOREIGN KEY("from_bank_account_id") REFERENCES "accounts"("id");
