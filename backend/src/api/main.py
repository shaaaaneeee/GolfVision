import os
import uuid
import tempfile
import threading
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # reads backend/.env if present

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from api.models import AnalysisJob, AnalysisResult, FaultResult
from api.worker import run_analysis

app = FastAPI(title="GolfVision API")

_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list({_frontend_url, "http://localhost:3000"}),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

# In-memory job store.
# To restore Redis/RQ: replace with redis.from_url() + rq.Queue and swap the
# enqueue/fetch calls below back to the RQ versions.
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _process_job(job_id: str, video_path: str, skill_level: str) -> None:
    """Runs the analysis pipeline in a background thread."""
    try:
        result = run_analysis(video_path, skill_level)
        payload = {"status": "failed", "error": result["error"]} if result.get("error") else {
            "status": "complete",
            "faults": result.get("faults", {}),
            "coaching": result.get("coaching", ""),
            "features": result.get("features", {}),
        }
    except Exception:
        payload = {"status": "failed", "error": "Analysis failed. Please try again."}
    with _jobs_lock:
        _jobs[job_id] = payload


@app.post("/analyze", response_model=AnalysisJob)
async def analyze(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    skill_level: str = Form(default="intermediate"),
):
    contents = await video.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Video file too large. Maximum size is 50MB.")

    job_id = str(uuid.uuid4())
    suffix = Path(video.filename or "swing.mp4").suffix or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(contents)
    tmp.close()

    with _jobs_lock:
        _jobs[job_id] = {"status": "processing"}

    background_tasks.add_task(_process_job, job_id, tmp.name, skill_level)
    return AnalysisJob(job_id=job_id)


@app.get("/result/{job_id}", response_model=AnalysisResult)
def get_result(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    status = job["status"]

    if status == "processing":
        return AnalysisResult(job_id=job_id, status="processing")

    if status == "failed":
        return AnalysisResult(job_id=job_id, status="failed", error=job.get("error"))

    faults = [FaultResult(name=k, severity=v) for k, v in job.get("faults", {}).items()]
    return AnalysisResult(
        job_id=job_id,
        status="complete",
        faults=faults,
        coaching=job.get("coaching"),
        features=job.get("features"),
    )
