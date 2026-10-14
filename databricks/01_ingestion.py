
import os
from pathlib import Path

from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv

# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

LOCAL_CSV = PROJECT_ROOT / "data" / "orders.csv"
VOLUME_PATH = "/Volumes/workspace/default/ai_quality_files/orders.csv"
BRONZE_TABLE = "workspace.default.orders_bronze"

WAREHOUSE_ID = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

EXPECTED_COLUMNS = [
    "order_id",
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "unit_price",
    "city",
    "payment_method",
]

EXPECTED_ROW_COUNT = 1000

client = WorkspaceClient(
    host=os.getenv("DATABRICKS_HOST"),
    profile="dbc-43e699c4-9a50",
)


# --------------------------------------------------
# SQL execution
# --------------------------------------------------

def execute_sql(statement):
    if not WAREHOUSE_ID:
        raise RuntimeError(
            "DATABRICKS_SQL_WAREHOUSE_ID is missing from .env"
        )

    response = client.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=statement,
        wait_timeout="30s",
    )

    state = response.status.state if response.status else None
    state_name = getattr(state, "name", str(state))

    if state_name != "SUCCEEDED":
        statement_id = response.statement_id

        try:
            details = client.statement_execution.get_statement(
                statement_id=statement_id
            )
            print(f"\nDatabricks SQL status: {details.status}")
            print(f"Statement ID: {statement_id}")
        except Exception:
            print(f"Statement ID: {statement_id}")

        raise RuntimeError(
            f"Databricks SQL failed with status: {state_name}"
        )

    return response


# --------------------------------------------------
# Upload CSV to Databricks Volume
# --------------------------------------------------

def upload_csv():
    if not LOCAL_CSV.exists():
        raise FileNotFoundError(
            f"Orders CSV not found: {LOCAL_CSV}"
        )

    with LOCAL_CSV.open("rb") as file:
        client.files.upload(
            file_path=VOLUME_PATH,
            contents=file,
            overwrite=True,
        )

    print(f"CSV uploaded successfully: {VOLUME_PATH}")


# --------------------------------------------------
# Create Bronze table if necessary
# --------------------------------------------------

def create_bronze_table():
    execute_sql(f"""
        CREATE TABLE IF NOT EXISTS {BRONZE_TABLE} (
            order_id STRING,
            customer_id STRING,
            product_id STRING,
            order_date DATE,
            quantity INT,
            unit_price DOUBLE,
            city STRING,
            payment_method STRING
        )
        USING DELTA
    """)


# --------------------------------------------------
# Inspect Bronze schema
# --------------------------------------------------

def get_bronze_columns():
    result = execute_sql(
        f"DESCRIBE TABLE {BRONZE_TABLE}"
    )

    rows = result.result.data_array if result.result else []
    columns = []

    for row in rows:
        name = str(row[0]).strip().lower()

        if name and not name.startswith("#"):
            columns.append(name)

    missing = [
        column for column in EXPECTED_COLUMNS
        if column not in columns
    ]

    if missing:
        raise RuntimeError(
            f"Bronze table is missing expected columns: {missing}. "
            f"Detected columns: {columns}"
        )

    extra_columns = [
        column for column in columns
        if column not in EXPECTED_COLUMNS
    ]

    unsupported = [
        column for column in extra_columns
        if column != "_rescued_data"
    ]

    if unsupported:
        raise RuntimeError(
            f"Unexpected Bronze columns: {unsupported}. "
            "No ingestion overwrite was performed."
        )

    return columns


# --------------------------------------------------
# Ingest CSV into Bronze
# --------------------------------------------------

def ingest_bronze():
    print("Preparing Bronze table...")
    create_bronze_table()

    print("Inspecting Bronze table schema...")
    target_columns = get_bronze_columns()
    print(f"Detected columns: {target_columns}")

    select_expressions = [
        (
            f"CAST(`{column}` AS "
            f"{'DATE' if column == 'order_date' else 'INT' if column == 'quantity' else 'DOUBLE' if column == 'unit_price' else 'STRING'}) "
            f"AS `{column}`"
        )
        for column in EXPECTED_COLUMNS
    ]

    if "_rescued_data" in target_columns:
        select_expressions.append(
            "CAST(NULL AS STRING) AS `_rescued_data`"
        )

    target_list = ", ".join(
        f"`{column}`" for column in target_columns
    )
    select_list = ",\n            ".join(select_expressions)

    print("Loading CSV records into Bronze...")

    execute_sql(f"""
        INSERT OVERWRITE TABLE {BRONZE_TABLE}
            ({target_list})
        SELECT
            {select_list}
        FROM read_files(
            '{VOLUME_PATH}',
            format => 'csv',
            header => true,
            inferSchema => true
        )
    """)

    result = execute_sql(f"""
        SELECT COUNT(*) AS total_rows
        FROM {BRONZE_TABLE}
    """)

    rows = result.result.data_array if result.result else []

    if not rows:
        raise RuntimeError(
            "The row-count query returned no results."
        )

    count = int(rows[0][0])

    print(f"\nBronze ingestion completed. Rows loaded: {count}")

    if count != EXPECTED_ROW_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_ROW_COUNT} rows, but found {count}."
        )

    print("Validation passed: all 1000 records loaded.")


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":
    try:
        upload_csv()
        ingest_bronze()
        print("\nIngestion completed successfully.")

    except Exception as error:
        print(f"\nINGESTION FAILED: {error}")
        raise
