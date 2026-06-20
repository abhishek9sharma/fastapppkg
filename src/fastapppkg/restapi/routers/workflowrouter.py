import os
import uuid

from fastapi import APIRouter, HTTPException
from temporalio.client import Client

from fastapppkg.temporal.workflows import PrintWorkflow

router = APIRouter()

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "print-workflow-queue"


@router.post("/run")
async def run_workflow():
    try:
        client = await Client.connect(TEMPORAL_HOST)
        workflow_id = f"print-workflow-{uuid.uuid4()}"
        result = await client.execute_workflow(
            PrintWorkflow.run,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )
        return {"workflow_id": workflow_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
