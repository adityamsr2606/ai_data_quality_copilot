
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
RESULTS_TABLE = "workspace.default.data_quality_results"

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


def get_scalar(statement):
    result = execute_sql(statement)
    rows = result.result.data_array if result.result else []

    if not rows:
        raise RuntimeError(
            "A quality-check query returned no results."
        )

    return int(rows[0][0])


# --------------------------------------------------
# Define automated quality checks
# --------------------------------------------------

def run_quality_checks():
    print("Running data-quality checks...")

    checks = [
        {
            "dataset": "orders",
            "check_name": "duplicate_order_id",
            "sql": f"""
                SELECT COUNT(*)
                FROM (
                    SELECT order_id
                    FROM {BRONZE_TABLE}
                    GROUP BY order_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """,
        },
        {
            "dataset": "orders",
            "check_name": "missing_customer_id",
            "sql": f"""
                SELECT COUNT(*)
                FROM {BRONZE_TABLE}
                WHERE customer_id IS NULL
                   OR TRIM(customer_id) = ''
            """,
        },
        {
            "dataset": "orders",
            "check_name": "missing_unit_price",
            "sql": f"""
                SELECT COUNT(*)
                FROM {BRONZE_TABLE}
                WHERE unit_price IS NULL
            """,
        },
        {
            "dataset": "orders",
            "check_name": "negative_quantity",
            "sql": f"""
                SELECT COUNT(*)
                FROM {BRONZE_TABLE}
                WHERE quantity IS NULL OR quantity <= 0
            """,
        },
        {
            "dataset": "orders",
            "check_name": "invalid_payment_method",
            "sql": f"""
                SELECT COUNT(*)
                FROM {BRONZE_TABLE}
                WHERE payment_method IS NULL
                   OR LOWER(TRIM(payment_method))
                      NOT IN ({VALID_PAYMENT_METHODS})
            """,
        },
        {
            "dataset": "orders_silver",
            "check_name": "silver_duplicate_order_id",
            "sql": f"""
                SELECT COUNT(*)
                FROM (
                    SELECT order_id
                    FROM {SILVER_TABLE}
                    GROUP BY order_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """,
        },
        {
            "dataset": "orders_silver",
            "check_name": "silver_missing_required_fields",
            "sql": f"""
                SELECT COUNT(*)
                FROM {SILVER_TABLE}
                WHERE order_id IS NULL
                   OR TRIM(order_id) = ''
                   OR customer_id IS NULL
                   OR TRIM(customer_id) = ''
                   OR product_id IS NULL
                   OR TRIM(product_id) = ''
                   OR order_date IS NULL
                   OR quantity IS NULL
                   OR quantity <= 0
                   OR unit_price IS NULL
                   OR unit_price < 0
                   OR payment_method IS NULL
                   OR TRIM(payment_method) = ''
            """,
        },
        {
            "dataset": "orders",
            "check_name": "bronze_silver_reconciliation",
            "sql": f"""
                SELECT ABS(
                    (SELECT COUNT(*) FROM {BRONZE_TABLE})
                    -
                    (SELECT COUNT(*) FROM {SILVER_TABLE})
                    -
                    (SELECT COUNT(*) FROM {QUARANTINE_TABLE})
                )
            """,
        },
    ]

    results = []

    for check in checks:
        failed_records = get_scalar(check["sql"])
        passed = failed_records == 0

        results.append(
            (
                check["dataset"],
                check["check_name"],
                "PASS" if passed else "FAIL",
                failed_records,
            )
        )

        print(
            f'{check["check_name"]}: '
            f'{"PASS" if passed else "FAIL"} '
            f'(failed_records={failed_records})'
        )

    return results


# --------------------------------------------------
# Save results to Delta
# --------------------------------------------------

def save_results(results):
    print("\nSaving quality results to Databricks...")

    execute_sql(f"""
        CREATE TABLE IF NOT EXISTS {RESULTS_TABLE} (
            dataset STRING,
            check_name STRING,
            status STRING,
            failed_records BIGINT
        )
        USING DELTA
    """)

    values = []

    for dataset, check_name, status, failed_records in results:
        dataset_sql = dataset.replace("'", "''")
        check_sql = check_name.replace("'", "''")
        status_sql = status.replace("'", "''")

        values.append(
            f"('{dataset_sql}', '{check_sql}', "
            f"'{status_sql}', {int(failed_records)})"
        )

    values_sql = ",\n".join(values)

    execute_sql(f"""
        INSERT OVERWRITE TABLE {RESULTS_TABLE}
            (dataset, check_name, status, failed_records)
        SELECT
            dataset,
            check_name,
            status,
            failed_records
        FROM VALUES
            {values_sql}
        AS quality_results(
            dataset,
            check_name,
            status,
            failed_records
        )
    """)

    print(f"Saved {len(results)} quality checks.")


# --------------------------------------------------
# Display final report
# --------------------------------------------------

def show_summary():
    result = execute_sql(f"""
        SELECT dataset, check_name, status, failed_records
        FROM {RESULTS_TABLE}
        ORDER BY dataset, check_name
    """)

    rows = result.result.data_array if result.result else []

    print("\n========== DATA QUALITY REPORT ==========")

    for row in rows:
        print(
            f"Dataset: {row[0]} | "
            f"Check: {row[1]} | "
            f"Status: {row[2]} | "
            f"Failed records: {row[3]}"
        )

    print("=========================================")


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":
    try:
        quality_results = run_quality_checks()
        save_results(quality_results)
        show_summary()

        print("\nData-quality checks completed successfully.")

    except Exception as error:
        print(f"\nDATA QUALITY CHECKS FAILED: {error}")
        raise
