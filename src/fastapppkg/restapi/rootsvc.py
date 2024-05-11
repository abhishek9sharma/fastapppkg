from fastapi import FastAPI

from fastapppkg.mathops.ops import addop
from fastapppkg.restapi.routers import mathopsrouter
from fastapppkg.schemas.mathops import MathOpsReq, MathOpsResp

app = FastAPI()


@app.get("/")
def start_svc():
    return {"Info": "Root Service is running"}


@app.post("/add")
def add(add_req: MathOpsReq):
    ans2 = addop(add_req.num_1, add_req.num_2)
    return {"ans": ans2}


app.include_router(mathopsrouter.router, prefix="/mathops")
