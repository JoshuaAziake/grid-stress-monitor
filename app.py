from flask import Flask, jsonify, request
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
    try:
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        return jsonify({"postgres": version})
    finally:
        conn.close()

@app.route("/api/ramp-rates")
def ramp_rates():
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "start and end query parameters required"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            WITH hourly_ramps AS (
                SELECT
                    DATE(timestamp) AS day,
                    ABS(value_mw - LAG(value_mw) OVER (ORDER BY timestamp)) AS ramp_mw
                FROM generation
                WHERE respondent = 'ERCO'
                  AND fueltype = 'NG'
                  AND timestamp >= %s
                  AND timestamp < %s
            )
            SELECT
                day,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ramp_mw) AS p25,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ramp_mw) AS median,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ramp_mw) AS p75,
                MAX(ramp_mw) AS max_ramp_mw
            FROM hourly_ramps
            WHERE ramp_mw IS NOT NULL
            GROUP BY day
            ORDER BY day;
        """, (start, end))
        rows = cur.fetchall()
        cur.close()
        result = [
            {
                "date": str(row[0]),
                "p25": float(row[1]),
                "median": float(row[2]),
                "p75": float(row[3]),
                "max_ramp_mw": float(row[4])
            }
            for row in rows
        ]
        return jsonify(result)
    finally:
        conn.close()

@app.route("/api/renewable-penetration")
def renewable_penetration():
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "start and end query parameters required"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                DATE(timestamp) AS day,
                SUM(CASE WHEN fueltype IN ('WND', 'SUN') THEN value_mw ELSE 0 END) /
                NULLIF(SUM(value_mw), 0) AS vre_fraction
            FROM generation
            WHERE respondent = 'ERCO'
              AND timestamp >= %s
              AND timestamp < %s
              AND value_mw IS NOT NULL
            GROUP BY day
            ORDER BY day;
        """, (start, end))
        rows = cur.fetchall()
        cur.close()
        result = [
            {
                "date": str(row[0]),
                "vre_fraction": round(float(row[1]), 4)
            }
            for row in rows
        ]
        return jsonify(result)
    finally:
        conn.close()

@app.route("/api/duck-curve")
def duck_curve():
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "start and end query parameters required"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                EXTRACT(HOUR FROM timestamp)::int AS hour,
                AVG(CASE WHEN fueltype = 'WND' THEN value_mw END) AS wnd,
                AVG(CASE WHEN fueltype = 'SUN' THEN value_mw END) AS sun,
                AVG(CASE WHEN fueltype = 'NG'  THEN value_mw END) AS ng
            FROM generation
            WHERE respondent = 'ERCO'
              AND timestamp >= %s
              AND timestamp < %s
              AND value_mw IS NOT NULL
            GROUP BY hour
            ORDER BY hour;
        """, (start, end))
        rows = cur.fetchall()
        cur.close()
        result = [
            {
                "hour": row[0],
                "WND": round(float(row[1]), 1) if row[1] is not None else None,
                "SUN": round(float(row[2]), 1) if row[2] is not None else None,
                "NG":  round(float(row[3]), 1) if row[3] is not None else None
            }
            for row in rows
        ]
        return jsonify(result)
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
