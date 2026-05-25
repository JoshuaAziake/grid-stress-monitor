import os
import requests
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta

# Load environment variables from .env
load_dotenv()

EIA_API_KEY = os.getenv("EIA_API_KEY")
DB_HOST = os.getenv("GRIDDB_HOST")
DB_NAME = os.getenv("GRIDDB_NAME")
DB_USER = os.getenv("GRIDDB_USER")
DB_PASSWORD = os.getenv("GRIDDB_PASSWORD")

def fetch_eia_data(start, end):
    url = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data"
    params = {
            "api_key": EIA_API_KEY,
            "frequency": "hourly",
            "data[]": "value",
            "facets[respondent][]": "ERCO",
            "facets[fueltype][]": ["WND", "SUN", "NG"],
            "start": start,
            "end": end,
            "length": 5000,
            "offset": 0,
            }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def insert_records(records):
    conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
            )
    cursor = conn.cursor()

    for record in records:
        cursor.execute("""
            INSERT INTO generation (timestamp, respondent, fueltype, value_mw)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (timestamp, respondent, fueltype) DO NOTHING
            """, (
                datetime.strptime(record["period"], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc),
                record["respondent"],
                record["fueltype"],
                record["value"]
                ))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(records)} records.")

if __name__ == "__main__":
    conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
            )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(timestamp) FROM generation WHERE respondent = 'ERCO'
    """)
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    if result is None:
        start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    else:
        start = result + relativedelta(hours=1)

    now = datetime.now(tz=timezone.utc)
    start_str = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H")
    end_str = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H")

    print(f"Fetching EIA data from {start_str} to {end_str}...")
    response = fetch_eia_data(start_str, end_str)
    records = response["response"]["data"]
    print(f"Retrieved {len(records)} records from EIA.")

    if records:
        insert_records(records)
