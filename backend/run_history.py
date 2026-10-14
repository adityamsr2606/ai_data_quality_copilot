
from backend.database import get_connection


def _fetch_one(cursor):
    row = cursor.fetchone()
    if row is None:
        return None

    columns = [item[0] for item in cursor.description]
    return dict(zip(columns, row))


def _fetch_all(cursor):
    columns = [item[0] for item in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def create_run(pipeline_name="AI Data Quality Copilot"):
    """Create a run and return its PostgreSQL-generated integer ID."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.pipeline_runs
                    (pipeline_name, status, records_processed, error_message)
                VALUES (%s, %s, %s, %s)
                RETURNING run_id, pipeline_name, status, run_time
                """,
                (pipeline_name, "RUNNING", 0, None),
            )
            result = _fetch_one(cursor)

        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def finish_run(
    run_id,
    status,
    records_processed=0,
    error_message=None,
    quality_results=None,
):
    """Finish a run and optionally store its quality-check results."""
    valid_statuses = {"SUCCESS", "FAILED", "COMPLETED", "PARTIAL"}

    if status not in valid_statuses:
        raise ValueError(
            f"Invalid final status: {status}. "
            f"Expected one of {sorted(valid_statuses)}"
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.pipeline_runs
                SET status = %s,
                    records_processed = %s,
                    error_message = %s
                WHERE run_id = %s
                RETURNING run_id
                """,
                (status, max(0, int(records_processed or 0)),
                 error_message, int(run_id)),
            )

            if cursor.fetchone() is None:
                raise ValueError(f"Pipeline run {run_id} was not found.")

            for item in quality_results or []:
                check_status = str(item.get("status", "UNKNOWN")).upper()
                if check_status not in {"PASS", "FAIL", "UNKNOWN"}:
                    check_status = "UNKNOWN"

                failed_records = max(
                    0, int(item.get("failed_records", 0) or 0)
                )

                cursor.execute(
                    """
                    INSERT INTO public.pipeline_run_quality_results
                        (run_id, dataset, check_name, status, failed_records)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (run_id, check_name)
                    DO UPDATE SET
                        dataset = EXCLUDED.dataset,
                        status = EXCLUDED.status,
                        failed_records = EXCLUDED.failed_records
                    """,
                    (
                        int(run_id),
                        item.get("dataset"),
                        item.get("check_name", "unnamed_check"),
                        check_status,
                        failed_records,
                    ),
                )

        connection.commit()
        return get_run_detail(int(run_id))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_run_history(limit=25, offset=0):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    r.run_id,
                    r.pipeline_name,
                    r.status,
                    r.records_processed,
                    r.run_time,
                    r.error_message,
                    COUNT(q.id) AS total_checks,
                    COUNT(q.id) FILTER (WHERE q.status = 'PASS')
                        AS passed_checks,
                    COUNT(q.id) FILTER (WHERE q.status = 'FAIL')
                        AS failed_checks
                FROM public.pipeline_runs r
                LEFT JOIN public.pipeline_run_quality_results q
                    ON q.run_id = r.run_id
                GROUP BY r.run_id
                ORDER BY r.run_time DESC, r.run_id DESC
                LIMIT %s OFFSET %s
                """,
                (max(1, min(int(limit), 200)), max(0, int(offset))),
            )
            return _fetch_all(cursor)
    finally:
        connection.close()


def get_run_detail(run_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT run_id, pipeline_name, status,
                       records_processed, run_time, error_message
                FROM public.pipeline_runs
                WHERE run_id = %s
                """,
                (int(run_id),),
            )
            run = _fetch_one(cursor)

            if run is None:
                return None

            cursor.execute(
                """
                SELECT id, dataset, check_name, status,
                       failed_records, created_at
                FROM public.pipeline_run_quality_results
                WHERE run_id = %s
                ORDER BY created_at DESC, id DESC
                """,
                (int(run_id),),
            )
            run["quality_results"] = _fetch_all(cursor)
            return run
    finally:
        connection.close()


def get_run_summary():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_runs,
                    COUNT(*) FILTER (WHERE status = 'RUNNING')
                        AS running_runs,
                    COUNT(*) FILTER (
                        WHERE status IN ('SUCCESS', 'COMPLETED')
                    ) AS successful_runs,
                    COUNT(*) FILTER (WHERE status = 'FAILED')
                        AS failed_runs,
                    COALESCE(SUM(records_processed), 0)
                        AS total_records_processed,
                    MAX(run_time) AS last_run_time
                FROM public.pipeline_runs
                """
            )
            return _fetch_one(cursor)
    finally:
        connection.close()
