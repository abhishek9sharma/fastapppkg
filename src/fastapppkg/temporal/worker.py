import asyncio
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "print-workflow-queue"


async def run_worker():
    logger.info(f"Worker task started, connecting to {TEMPORAL_HOST}")
    for attempt in range(1, 11):
        try:
            client = await asyncio.wait_for(
                Client.connect(TEMPORAL_HOST), timeout=10
            )
            worker = Worker(
                client,
                task_queue=TASK_QUEUE,
                workflows=[PrintWorkflow],
                activities=[print_step_one, print_step_two, print_step_three, print_step_four],
            )
            logger.info(f"Worker connected to Temporal at {TEMPORAL_HOST}")
            await worker.run()
            return
        except Exception as e:
            logger.error(f"Worker attempt {attempt}/10 failed: {e}")
            if attempt == 10:
                raise
            await asyncio.sleep(5 * attempt)
