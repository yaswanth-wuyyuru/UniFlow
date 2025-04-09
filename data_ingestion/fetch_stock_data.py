import http.client
import json
import pandas as pd
import snowflake.connector
import os
from datetime import datetime, timezone

# 🔁 Stock symbols to fetch
SYMBOLS = ["tsla", "aapl", "msft", "nvda", "amd", "tsm"]

# ✅ Get secrets from GitHub Actions ENV
def get_env_secrets():
    return {
        "rapidapi_key": os.environ.get("rapidapi_key"),
        "snowflake_user": os.environ.get("snowflake_username"),
        "snowflake_password": os.environ.get("snowflake_password"),
        "snowflake_account": os.environ.get("snowflake_account"),
        "snowflake_warehouse": os.environ.get("snowflake_warehouse"),
        "snowflake_database": os.environ.get("snowflake_database"),
        "snowflake_schema": os.environ.get("snowflake_schema")
    }

# 📊 Fetch analytics data for one stock
def fetch_stock_analytics(symbol, api_key):
    try:
        conn = http.client.HTTPSConnection("yahoo-finance127.p.rapidapi.com")
        endpoint = f"/finance-analytics/{symbol}"

        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "yahoo-finance127.p.rapidapi.com"
        }

        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()
        parsed = json.loads(data.decode("utf-8"))

        print(f"📦 {symbol.upper()} Analytics Response:")
        print(json.dumps(parsed, indent=2))

        if isinstance(parsed, dict):
            df = pd.DataFrame([parsed])
            df["symbol"] = symbol.upper()
            df["fetched_at"] = datetime.now(timezone.utc).isoformat()
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error fetching {symbol.upper()}: {e}")
        return pd.DataFrame()

# 🔐 Connect to Snowflake (using passed-in secrets)
def connect_snowflake(secrets):
    return snowflake.connector.connect(
        user=secrets["snowflake_username"],
        password=secrets["snowflake_password"],
        account=secrets["snowflake_account"],
        warehouse=secrets["snowflake_warehouse"],
        database=secrets["snowflake_database"],
        schema=secrets["snowflake_schema"]
    )

# 💾 Load data into Snowflake
def load_analytics_to_snowflake(df, secrets):
    if df.empty:
        print("⚠️ No analytics data to load.")
        return

    conn = connect_snowflake(secrets)
    cursor = conn.cursor()

    create_stmt = """
    CREATE TABLE IF NOT EXISTS STOCK_ANALYTICS (
        symbol STRING,
        price FLOAT,
        target_high FLOAT,
        target_low FLOAT,
        target_mean FLOAT,
        recommendation STRING,
        analyst_count INT,
        fetched_at STRING
    );
    """
    cursor.execute(create_stmt)

    insert_stmt = """
    INSERT INTO STOCK_ANALYTICS (
        symbol, price, target_high, target_low,
        target_mean, recommendation, analyst_count, fetched_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    for _, row in df.iterrows():
        try:
            cursor.execute(insert_stmt, (
                row.get("symbol"),
                row.get("currentPrice", {}).get("raw"),
                row.get("targetHighPrice", {}).get("raw"),
                row.get("targetLowPrice", {}).get("raw"),
                row.get("targetMeanPrice", {}).get("raw"),
                row.get("recommendationKey"),
                row.get("numberOfAnalystOpinions", {}).get("raw"),
                row.get("fetched_at")
            ))
        except Exception as e:
            print(f"❌ Error inserting {row.get('symbol')}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Inserted {len(df)} records into RAW.STOCK_ANALYTICS")

# 🏁 Main execution
if __name__ == "__main__":
    secrets = get_env_secrets()
    all_data = []

    for symbol in SYMBOLS:
        df = fetch_stock_analytics(symbol, secrets["rapidapi_key"])
        if not df.empty:
            all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        load_analytics_to_snowflake(final_df, secrets)
    else:
        print(" No data fetched for any symbol.")
