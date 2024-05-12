from fastapi import FastAPI
from fastapppkg.mathops.ops import addop
from fastapppkg.restapi.routers import mathopsrouter
from fastapppkg.schemas.mathops import MathOpsReq, MathOpsResp

app = FastAPI()


@app.get("/")
def start_svc():
    """This function is used to start the root service.

    Returns:
        A dictionary containing information that the Root Service is running.
    """
    return {"Info": "Root Service is running"}


@app.post("/add")
def add(add_req: MathOpsReq):
    """Performs addition operation on two numbers.

    Args:
        add_req: An object containing the two numbers to be added.

    Returns:
        A dictionary containing the result of the addition operation.
    """
    ans2 = addop(add_req.num_1, add_req.num_2)
    return {"ans": ans2}


app.include_router(mathopsrouter.router, prefix="/mathops")
