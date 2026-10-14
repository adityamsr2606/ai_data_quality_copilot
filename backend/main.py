
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from backend.database import get_connection
from backend.databricks_client import (
    test_databricks_connection,
    get_quality_results,
    get_overview,
    get_table_preview,
)
from backend import run_history

app = FastAPI(
    title="AI Data Quality Copilot API",
    description="Data quality monitoring, pipeline observability, and run history API",
    version="2.1.0",
)


# =========================================================
# Request models
# =========================================================

class PipelineRunCreate(BaseModel):
    pipeline_name: str = Field(
        default="AI Data Quality Copilot",
        min_length=1,
        max_length=200,
    )


class QualityResultInput(BaseModel):
    dataset: Optional[str] = None
    check_name: str = Field(default="unnamed_check", min_length=1, max_length=200)
    status: str = "UNKNOWN"
    failed_records: int = Field(default=0, ge=0)


class PipelineRunFinish(BaseModel):
    status: str = Field(default="SUCCESS")
    records_processed: int = Field(default=0, ge=0)
    error_message: Optional[str] = None
    quality_results: list[QualityResultInput] = Field(default_factory=list)


# =========================================================
# Core health and dashboard endpoints
# =========================================================

@app.get("/")
def home():
    return {
        "message": "AI Data Quality Copilot API is running",
        "version": "2.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    try:
        conn = get_connection()
        conn.close()

        return {
            "status": "healthy",
            "postgresql": "connected",
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "postgresql": "connection failed",
            "error": str(exc),
        }


@app.get("/databricks-health")
def databricks_health():
    result = test_databricks_connection()

    if result.get("status") != "connected":
        raise HTTPException(status_code=503, detail=result)

    return result


@app.get("/quality-results")
def quality_results():
    try:
        return get_quality_results()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve quality results: {exc}",
        ) from exc


@app.get("/overview")
def overview():
    try:
        return get_overview()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve dashboard metrics: {exc}",
        ) from exc


@app.get("/records/{layer}")
def records(
    layer: str,
    limit: int = Query(default=100, ge=1, le=500),
):
    try:
        return get_table_preview(layer, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve table records: {exc}",
        ) from exc


# =========================================================
# Quality-result synchronization
# =========================================================

@app.post("/sync-quality-results")
def sync_quality_results():
    conn = None
    cursor = None

    try:
        results = get_quality_results()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM data_quality_results")

        for result in results:
            cursor.execute(
                """
                INSERT INTO data_quality_results
                    (dataset, check_name, status, failed_records)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    result["dataset"],
                    result["check_name"],
                    result["status"],
                    int(result["failed_records"]),
                ),
            )

        conn.commit()

        return {
            "status": "success",
            "records_synced": len(results),
        }

    except Exception as exc:
        if conn is not None:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Quality-result synchronization failed: {exc}",
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


# =========================================================
# Pipeline run history
# =========================================================

@app.post("/pipeline-runs", status_code=201)
def start_pipeline_run(payload: PipelineRunCreate):
    try:
        return run_history.create_run(payload.pipeline_name)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not start pipeline run: {exc}",
        ) from exc


@app.patch("/pipeline-runs/{run_id}/finish")
def complete_pipeline_run(run_id: int, payload: PipelineRunFinish):
    try:
        quality_results_data: list[dict[str, Any]] = [
            item.model_dump() for item in payload.quality_results
        ]

        result = run_history.finish_run(
            run_id=run_id,
            status=payload.status.upper(),
            records_processed=payload.records_processed,
            error_message=payload.error_message,
            quality_results=quality_results_data,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline run {run_id} was not found",
            )

        return result

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not finish pipeline run: {exc}",
        ) from exc


@app.get("/pipeline-runs/summary")
def pipeline_run_summary():
    try:
        return run_history.get_run_summary()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve run summary: {exc}",
        ) from exc


@app.get("/pipeline-runs")
def pipeline_run_list(
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        return run_history.get_run_history(limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve pipeline run history: {exc}",
        ) from exc


@app.get("/pipeline-runs/{run_id}")
def pipeline_run_detail(run_id: int):
    try:
        result = run_history.get_run_detail(run_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline run {run_id} was not found",
            )

        return result

    except HTTPException:
        raise
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid run ID") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve pipeline run: {exc}",
        ) from exc
