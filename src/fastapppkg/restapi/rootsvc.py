import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapppkg.mathops.ops import addop
from fastapppkg.restapi.routers import mathopsrouter
from fastapppkg.restapi.routers import workflowrouter
from fastapppkg.schemas.mathops import MathOpsReq, MathOpsResp
from fastapppkg.temporal.worker import run_worker


def _log_worker_error(task):
    if not task.cancelled() and not task.exception() is None:
        import logging
        logging.getLogger(__name__).error("Worker task failed", exc_info=task.exception())


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(run_worker())
    worker_task.add_done_callback(_log_worker_error)
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


@app.get("/")
def start_svc():
    return {"Info": "Root Service is running"}


@app.post("/add")
def add(add_req: MathOpsReq):
    ans2 = addop(add_req.num_1, add_req.num_2)
    return {"ans": ans2}


app.include_router(mathopsrouter.router, prefix="/mathops")
app.include_router(workflowrouter.router, prefix="/workflow")
