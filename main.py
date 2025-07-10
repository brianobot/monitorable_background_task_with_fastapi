import uuid 
import time

from typing import Callable, Awaitable
from fastapi import FastAPI, BackgroundTasks, HTTPException


app = FastAPI()
task_store: dict[str, dict] = {}


def count_to(n: int, job_id: str, update_function: Callable[..., Awaitable[None]]):
    """
    Iterates from 1 up to n and returns the values of n

    This is meant to be used to represent a slow running function.
    """
    result = 1
    for i in range(1, n):
        update_function(job_id, "processing", (i / n) * 100)
        print(f"{i}")
        result = i

    update_function(job_id, "completed", 100, result, ended_at=time.time())
    return result


@app.post("/tasks")
async def initiate_task(background_task: BackgroundTasks):
    # generates unique id for each request
    job_id = str(uuid.uuid4())

    # register the task to the task db
    task_store[job_id] = {
        "status": "initiated",
        "progress": 0.0,
        "result": None,
        "errors": None,
        "started_at": time.time(),
        "ended_at": None,
    }

    def update_task(job_ib: str, status: str, progress: float | int, result = None, errors = None, ended_at = None):
        if not job_ib in task_store:
            # in this case the job was never registered so ignore it
            return
        
        task_store[job_id].update({
        "progress": progress,
        "status": status,
        "result": result,
        "errors": errors,
        "ended_at": ended_at,
    })

    # register the function (task) to be ran in the backgrund
    background_task.add_task(count_to, 1_000_000, job_id, update_task)

    # returns immediately to the client
    return {
        "message": "task started", 
        "job_id": job_id,
    }


@app.get("/tasks/status")
async def get_task_status(job_id: str):
    if not job_id in task_store:
        raise HTTPException(404, detail="Job ID not found")
    
    return task_store[job_id]