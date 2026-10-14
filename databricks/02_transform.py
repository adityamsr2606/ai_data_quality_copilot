
import os
from pathlib import Path

from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv

# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

WAREHOUSE_ID = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

BRONZE_TABLE = "workspace.default.orders_bronze"
SILVER_TABLE = "workspace.default.orders_silver"
QUARANTINE_TABLE = "workspace.default.orders_quarantine"

VALID_PAYMENT_METHODS = (
    "'card', 'cash', 'upi', 'net banking'"
)

client = WorkspaceClient(
    host=os.getenv("DATABRICKS_HOST"),
    profile="dbc-43e699c4-9a50",
)


# --------------------------------------------------
# Execute Databricks SQL
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
            print(f"Databricks SQL status: {details.status}")
        except Exception:
            pass

        raise RuntimeError(
            f"Databricks SQL failed: {state_name}. "
            f"Statement ID: {statement_id}"
        )

    return response


def get_count(table_name):
    result = execute_sql(
        f"SELECT COUNT(*) AS total FROM {table_name}"
    )

    rows = result.result.data_array if result.result else []

    if not rows:
        raise RuntimeError(
            f"Could not retrieve row count for {table_name}"
        )

    return int(rows[0][0])


# --------------------------------------------------
# Bronze-to-Silver transformation
# --------------------------------------------------

def transform_orders():
    print("Checking Bronze source...")

    bronze_count = get_count(BRONZE_TABLE)
    print(f"Bronze records available: {bronze_count}")

    if bronze_count == 0:
        raise RuntimeError(
            "Bronze table is empty. Run 01_ingestion.py first."
        )

    # --------------------------------------------------
    # Step 1: Quarantine invalid records
    # --------------------------------------------------

    print("Creating quarantine table...")

    execute_sql(f"""
        CREATE OR REPLACE TABLE {QUARANTINE_TABLE}
        USING DELTA
        AS
        WITH ranked AS (
            SELECT
                order_id,
                customer_id,
                product_id,
                order_date,
                quantity,
                unit_price,
                city,
                payment_method,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id
                    ORDER BY
                        customer_id NULLS LAST,
                        product_id NULLS LAST,
                        order_date NULLS LAST,
                        quantity NULLS LAST,
                        unit_price NULLS LAST
                ) AS duplicate_rank
            FROM {BRONZE_TABLE}
        ),
        classified AS (
            SELECT
                *,
                CASE
                    WHEN order_id IS NULL
                         OR TRIM(order_id) = ''
                        THEN 'missing_order_id'

                    WHEN duplicate_rank > 1
                        THEN 'duplicate_order_id'

                    WHEN customer_id IS NULL
                         OR TRIM(customer_id) = ''
                        THEN 'missing_customer_id'

                    WHEN quantity IS NULL OR quantity <= 0
                        THEN 'invalid_quantity'

                    WHEN unit_price IS NULL OR unit_price < 0
                        THEN 'invalid_unit_price'

                    WHEN payment_method IS NULL
                         OR LOWER(TRIM(payment_method))
                            NOT IN ({VALID_PAYMENT_METHODS})
                        THEN 'invalid_payment_method'

                    WHEN order_date IS NULL
                        THEN 'invalid_order_date'

                    ELSE NULL
                END AS rejection_reason
            FROM ranked
        )
        SELECT
            order_id,
            customer_id,
            product_id,
            order_date,
            quantity,
            unit_price,
            city,
            payment_method,
            rejection_reason,
            CURRENT_TIMESTAMP() AS quarantined_at
        FROM classified
        WHERE rejection_reason IS NOT NULL
    """)

    # --------------------------------------------------
    # Step 2: Create the clean Silver table
    # --------------------------------------------------

    print("Creating clean Silver table...")

    execute_sql(f"""
        CREATE OR REPLACE TABLE {SILVER_TABLE}
        USING DELTA
        AS
        WITH ranked AS (
            SELECT
                order_id,
                customer_id,
                product_id,
                order_date,
                quantity,
                unit_price,
                city,
                payment_method,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id
                    ORDER BY
                        customer_id NULLS LAST,
                        product_id NULLS LAST,
                        order_date NULLS LAST,
                        quantity NULLS LAST,
                        unit_price NULLS LAST
                ) AS duplicate_rank
            FROM {BRONZE_TABLE}
        )
        SELECT
            TRIM(order_id) AS order_id,
            TRIM(customer_id) AS customer_id,
            TRIM(product_id) AS product_id,
            order_date,
            quantity,
            unit_price,
            TRIM(city) AS city,
            INITCAP(TRIM(payment_method)) AS payment_method,
            ROUND(quantity * unit_price, 2) AS order_value,
            CURRENT_TIMESTAMP() AS processed_at
        FROM ranked
        WHERE duplicate_rank = 1
          AND order_id IS NOT NULL
          AND TRIM(order_id) <> ''
          AND customer_id IS NOT NULL
          AND TRIM(customer_id) <> ''
          AND quantity > 0
          AND unit_price IS NOT NULL
          AND unit_price >= 0
          AND order_date IS NOT NULL
          AND payment_method IS NOT NULL
          AND LOWER(TRIM(payment_method))
              IN ({VALID_PAYMENT_METHODS})
    """)

    # --------------------------------------------------
    # Step 3: Reconcile counts
    # --------------------------------------------------

    silver_count = get_count(SILVER_TABLE)
    quarantine_count = get_count(QUARANTINE_TABLE)

    accounted_count = silver_count + quarantine_count

    print("\n========== TRANSFORMATION SUMMARY ==========")
    print(f"Bronze records:     {bronze_count}")
    print(f"Silver records:     {silver_count}")
    print(f"Quarantined rows:   {quarantine_count}")
    print(f"Records accounted:  {accounted_count}")
    print("============================================")

    if accounted_count != bronze_count:
        raise RuntimeError(
            "Reconciliation failed: Bronze count does not equal "
            "Silver plus quarantine. Investigate before proceeding."
        )

    print("Reconciliation passed.")


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":
    try:
        transform_orders()
        print("\nBronze-to-Silver transformation completed.")
    except Exception as error:
        print(f"\nTRANSFORMATION FAILED: {error}")
        raise
