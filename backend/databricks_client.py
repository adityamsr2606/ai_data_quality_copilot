
import os
from pathlib import Path

from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

client = WorkspaceClient(
    host=os.getenv("DATABRICKS_HOST"),
    profile="dbc-43e699c4-9a50",
)

WAREHOUSE_ID = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

TABLES = {
    "bronze": "workspace.default.orders_bronze",
    "silver": "workspace.default.orders_silver",
    "quarantine": "workspace.default.orders_quarantine",
}


def execute_query(statement: str) -> list[dict]:
    """Execute a read-only query using the configured SQL warehouse."""

    if not WAREHOUSE_ID:
        raise RuntimeError(
            f"DATABRICKS_SQL_WAREHOUSE_ID is missing. Check {ENV_PATH}"
        )

    response = client.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=statement,
        wait_timeout="30s",
    )

    state = response.status.state if response.status else None
    state_name = getattr(state, "name", str(state))

    if state_name != "SUCCEEDED":
        raise RuntimeError(f"Databricks SQL query status: {state_name}")

    if not response.manifest:
        return []

    columns = [
        column.name
        for column in response.manifest.schema.columns
    ]

    rows = response.result.data_array if response.result else []

    return [dict(zip(columns, row)) for row in (rows or [])]


def test_databricks_connection():
    try:
        current_user = client.current_user.me()

        return {
            "status": "connected",
            "workspace": os.getenv("DATABRICKS_HOST"),
            "user": current_user.user_name,
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }


def get_quality_results():
    return execute_query(
        """
        SELECT dataset, check_name, status, failed_records
        FROM workspace.default.data_quality_results
        ORDER BY check_name
        """
    )


def get_overview():
    """Return live record counts and quality metrics."""

    counts = {}

    for layer, table_name in TABLES.items():
        result = execute_query(
            f"SELECT COUNT(*) AS total FROM {table_name}"
        )
        counts[layer] = int(result[0]["total"]) if result else 0

    quality_results = get_quality_results()

    total_checks = len(quality_results)
    passed_checks = sum(
        str(row.get("status", "")).upper() == "PASS"
        for row in quality_results
    )
    failed_checks = sum(
        str(row.get("status", "")).upper() == "FAIL"
        for row in quality_results
    )

    quality_score = (
        round(passed_checks / total_checks * 100, 1)
        if total_checks
        else 0
    )

    return {
        "records": {
            "bronze": counts["bronze"],
            "silver": counts["silver"],
            "quarantine": counts["quarantine"],
        },
        "quality": {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "score": quality_score,
        },
    }


def get_table_preview(layer: str, limit: int = 100):
    """Preview a whitelisted data layer without permitting arbitrary tables."""

    if layer not in TABLES:
        raise ValueError(
            f"Invalid layer. Choose one of: {', '.join(TABLES)}"
        )

    limit = max(1, min(int(limit), 500))
    table_name = TABLES[layer]

    return execute_query(
        f"SELECT * FROM {table_name} LIMIT {limit}"
    )
