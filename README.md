# Lakebase Form App

A minimal Databricks App (Flask) that inserts a row into a Postgres table
(Lakebase) when a form is submitted, and lists recent submissions.

## How the connection works

Lakebase doesn't use a static DB password. Your app's identity (a service
principal when deployed, your own user when running locally) requests a
short-lived OAuth token from Databricks and uses that token as the Postgres
password. Tokens expire after ~60 minutes, so `app.py` wraps `psycopg`'s
connection class to fetch a fresh token every time the pool opens a new
physical connection — you never manage token refresh by hand.

```
Flask route --> connection pool --> OAuthConnection.connect()
                                         |
                                         v
                          WorkspaceClient.postgres.generate_database_credential()
                                         |
                                         v
                                Postgres (Lakebase) via psycopg
```

## Setup

1. **Create the app.** In your Databricks workspace, create a new app from
   the "Flask Hello world" template. Note the `DATABRICKS_CLIENT_ID` shown
   on the app's Environment tab (a UUID) — this is the app's Postgres
   username.

2. **Create the database.** In the app switcher, open Lakebase Postgres and
   create a new project (Postgres 17 by default). Wait ~1 minute for
   compute to come up.

3. **Run `schema.sql`** in that project's SQL Editor, replacing every
   `<DATABRICKS_CLIENT_ID>` placeholder with the UUID from step 1. This
   creates the `submissions` table and grants the app's service principal
   access to it.

4. **Fill in `app.yaml`**: get `PGHOST` and the endpoint resource name from
   the Lakebase project's "Connect" modal (choose "Parameters only").

5. **Test locally**:
   ```bash
   databricks auth login
   export PGHOST="<your-endpoint-hostname>"
   export PGDATABASE="databricks_postgres"
   export PGUSER="your.email@company.com"   # your own identity for local runs
   export PGPORT="5432"
   export PGSSLMODE="require"
   export ENDPOINT_NAME="<your-endpoint-name>"

   pip3 install --upgrade -r requirements.txt
   python3 app.py
   ```
   Open http://localhost:8000, submit the form, confirm the row appears.

6. **Deploy**:
   ```bash
   databricks sync . /Workspace/Users/<your-email>/lakebase-form-app
   databricks apps deploy <app-name> \
     --source-code-path /Workspace/Users/<your-email>/lakebase-form-app
   ```

## Files

- `app.py` — Flask routes + Lakebase connection/token rotation
- `templates/index.html` — the submission form and results table
- `schema.sql` — one-time SQL: role, table, grants
- `app.yaml` — Databricks App run command + env vars
- `requirements.txt` — flask, psycopg, databricks-sdk
