from fastapi import APIRouter

from fastapppkg.mathops.ops import multop, subop
from fastapppkg.schemas.mathops import MathOpsReq, MathOpsResp

router = APIRouter()


@router.post("/sub")
def sub(add_req: MathOpsReq):
    ans = subop(add_req.num_1, add_req.num_2)
    return {"ans": ans}


@router.post("/mult")
def sub(add_req: MathOpsReq):
    ans = multop(add_req.num_1, add_req.num_2)
    return {"ans": ans}
