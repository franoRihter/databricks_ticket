import os
from flask import Flask, request, redirect, render_template, url_for
from databricks.sdk import WorkspaceClient
import psycopg
from psycopg_pool import ConnectionPool

app = Flask(__name__)

# --- 1. Databricks client used to mint short-lived Postgres credentials ---
w = WorkspaceClient()

# --- 2. Custom psycopg connection class that always fetches a fresh OAuth token ---
# Lakebase doesn't use a static password. Every new physical connection needs a
# token (valid ~60 min), so we override connect() to inject one each time.
class OAuthConnection(psycopg.Connection):
    @classmethod
    def connect(cls, conninfo="", **kwargs):
        endpoint_name = os.environ["ENDPOINT_NAME"]
        credential = w.postgres.generate_database_credential(endpoint=endpoint_name)
        kwargs["password"] = credential.token
        return super().connect(conninfo, **kwargs)

# --- 3. Connection parameters come from environment variables (set in app.yaml) ---
PGUSER = os.environ["PGUSER"]
PGHOST = os.environ["PGHOST"]
PGPORT = os.environ.get("PGPORT", "5432")
PGDATABASE = os.environ["PGDATABASE"]
PGSSLMODE = os.environ.get("PGSSLMODE", "require")

# --- 4. Pool of connections. The pool calls OAuthConnection.connect() whenever
# it needs a new physical connection, so tokens are rotated automatically. ---
pool = ConnectionPool(
    conninfo=f"dbname={PGDATABASE} user={PGUSER} host={PGHOST} port={PGPORT} sslmode={PGSSLMODE}",
    connection_class=OAuthConnection,
    min_size=1,
    max_size=10,
    open=True,
)


@app.route("/", methods=["GET"])
def index():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, message, created_at "
                "FROM submissions ORDER BY created_at DESC LIMIT 20"
            )
            rows = cur.fetchall()
    return render_template("index.html", rows=rows)


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not message:
        return redirect(url_for("index"))

    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Parameterized query -- never string-format user input into SQL.
            cur.execute(
                "INSERT INTO submissions (name, message) VALUES (%s, %s)",
                (name, message),
            )
        conn.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
