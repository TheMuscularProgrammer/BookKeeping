-- Generated from: https://drawsql.app/teams/get-shit-done/diagrams/oribookkeeping
-- How to connect: PGPASSWORD='example' psql -U postgres -h localhost -d mydatabase

CREATE TABLE "accounts"(
    "id" BIGINT NOT NULL,
    "owner_id" UUID NOT NULL
);
ALTER TABLE
    "accounts" ADD PRIMARY KEY("id");
CREATE TABLE "users"(
    "id" UUID NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);
CREATE INDEX "users_email_index" ON
    "users"("email");
ALTER TABLE
    "users" ADD PRIMARY KEY("id");
ALTER TABLE
    "users" ADD CONSTRAINT "users_email_unique" UNIQUE("email");
ALTER TABLE
    "accounts" ADD CONSTRAINT "accounts_owner_id_foreign" FOREIGN KEY("owner_id") REFERENCES "users"("id");
