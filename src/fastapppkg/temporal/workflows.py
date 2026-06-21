import asyncio
from datetime import timedelta

from temporalio import activity, workflow


@activity.defn
async def print_step_one() -> str:
    print("Step 1: Workflow started - initializing resources")
    await asyncio.sleep(3)
    return "step_one_complete"


@activity.defn
async def print_step_two() -> str:
    print("Step 2: Processing input data")
    await asyncio.sleep(3)
    return "step_two_complete"


@activity.defn
async def print_step_three() -> str:
    print("Step 3: Running business logic")
    await asyncio.sleep(3)
    return "step_three_complete"


@activity.defn
async def print_step_four() -> str:
    print("Step 4: Workflow complete - cleaning up")
    await asyncio.sleep(3)
    return "step_four_complete"


@workflow.defn
class PrintWorkflow:
    @workflow.run
    async def run(self) -> dict:
        r1 = await workflow.execute_activity(
            print_step_one, schedule_to_close_timeout=timedelta(seconds=30)
        )
        r2 = await workflow.execute_activity(
            print_step_two, schedule_to_close_timeout=timedelta(seconds=30)
        )
        r3 = await workflow.execute_activity(
            print_step_three, schedule_to_close_timeout=timedelta(seconds=30)
        )
        r4 = await workflow.execute_activity(
            print_step_four, schedule_to_close_timeout=timedelta(seconds=30)
        )
        return {"steps": [r1, r2, r3, r4], "status": "completed"}
