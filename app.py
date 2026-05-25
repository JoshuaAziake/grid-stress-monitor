from flask import Flask, jsonify
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
            host=os.environ.get("GRIDDB_HOST"),
            database=os.environ.get("GRIDDB_NAME"),
            user=os.environ.get("GRIDDB_USER"),
            password=os.environ.get("GRIDDB_PASSWORD")
            )

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/db")
def db_check():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    cur.close()
    conn.close()
    return jsonify({"postgres": version})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
