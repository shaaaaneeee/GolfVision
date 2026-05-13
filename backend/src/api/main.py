import os
import uuid
import tempfile
from pathlib import Path

import redis
from rq import Queue
from rq.job import Job
from rq.exceptions import NoSuchJobError
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import AnalysisJob, AnalysisResult, FaultResult

app = FastAPI(title="GolfVision API")

_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list({_frontend_url, "http://localhost:3000"}),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
_queue = Queue(connection=_redis)


@app.post("/analyze", response_model=AnalysisJob)
async def analyze(
    video: UploadFile = File(...),
    skill_level: str = Form(default="intermediate"),
):
    contents = await video.read()
    max_size = 50 * 1024 * 1024  # 50 MB
    if len(contents) > max_size:
        raise HTTPException(status_code=413, detail="Video file too large. Maximum size is 50MB.")

    job_id = str(uuid.uuid4())

    suffix = Path(video.filename or "swing.mp4").suffix or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(contents)
    tmp.close()

    _queue.enqueue(
        "api.worker.run_analysis",
        tmp.name,
        skill_level,
        job_id=job_id,
        result_ttl=3600,
    )
    return AnalysisJob(job_id=job_id)


@app.get("/result/{job_id}", response_model=AnalysisResult)
def get_result(job_id: str):
    try:
        job = Job.fetch(job_id, connection=_redis)
    except NoSuchJobError:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.is_finished:
        payload = job.result
        if payload.get("error"):
            return AnalysisResult(
                job_id=job_id,
                status="failed",
                error=payload["error"],
            )
        faults = [
            FaultResult(
                name=k,
                severity=v,
            )
            for k, v in payload["faults"].items()
        ]
        return AnalysisResult(
            job_id=job_id,
            status="complete",
            faults=faults,
            coaching=payload["coaching"],
            features=payload["features"],
        )

    if job.is_failed:
        return AnalysisResult(
            job_id=job_id,
            status="failed",
            error="Analysis failed. Please try again.",
        )

    return AnalysisResult(job_id=job_id, status="processing")
