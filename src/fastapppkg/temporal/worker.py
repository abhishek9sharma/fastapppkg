import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from fastapppkg.temporal.workflows import (
    PrintWorkflow,
    print_step_four,
    print_step_one,
    print_step_three,
    print_step_two,
)

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "print-workflow-queue"


async def run_worker():
    client = await Client.connect(TEMPORAL_HOST)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[PrintWorkflow],
        activities=[print_step_one, print_step_two, print_step_three, print_step_four],
    )
    print(f"Worker started — connected to Temporal at {TEMPORAL_HOST}")
    await worker.run()
