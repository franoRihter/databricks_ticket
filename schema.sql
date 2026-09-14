-- Run this once in the Lakebase project's SQL Editor.

-- 1. Enable OAuth-based auth (lets Postgres accept Databricks tokens instead of passwords)
CREATE EXTENSION IF NOT EXISTS databricks_auth;

-- 2. Create a Postgres role for the app's service principal.
--    Replace with the app's DATABRICKS_CLIENT_ID (Environment tab, after you create the app).
SELECT databricks_create_role('<DATABRICKS_CLIENT_ID>', 'service_principal');

GRANT CONNECT ON DATABASE databricks_postgres TO "<DATABRICKS_CLIENT_ID>";
GRANT CREATE, USAGE ON SCHEMA public TO "<DATABRICKS_CLIENT_ID>";

-- 3. The table the form writes into.
CREATE TABLE IF NOT EXISTS submissions (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    message    TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Service principals get no default privileges -- grant explicitly.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE submissions TO "<DATABRICKS_CLIENT_ID>";
GRANT USAGE, SELECT ON SEQUENCE submissions_id_seq TO "<DATABRICKS_CLIENT_ID>";
