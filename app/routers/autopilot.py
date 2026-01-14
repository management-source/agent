from fastapi import APIRouter
from typing import Optional
from app.services.gmail_sync import sync_inbox_threads
from app.scheduler import scheduler
from fastapi import HTTPException

router = APIRouter()

@router.post("/fetch-now")
def fetch_now(start: Optional[str] = None, end: Optional[str] = None, max_threads: int = 100):
    return sync_inbox_threads(max_threads=max_threads, start=start, end=end)

@router.post("/start")
def start_autopilot():
    job = scheduler.get_job("gmail_poll")
    if not job:
        raise HTTPException(500, "gmail_poll job not found")
    job.resume()
    return {"ok": True, "status": "started"}

@router.post("/stop")
def stop_autopilot():
    job = scheduler.get_job("gmail_poll")
    if not job:
        raise HTTPException(500, "gmail_poll job not found")
    job.pause()
    return {"ok": True, "status": "stopped"}

@router.get("/status")
def autopilot_status():
    job = scheduler.get_job("gmail_poll")
    if not job:
        return {"ok": True, "running": False, "next_run_time": None}
    return {"ok": True, "running": True, "next_run_time": str(job.next_run_time)}
