from fastapi import APIRouter
from fastapppkg.mathops.ops import multop, subop
from fastapppkg.schemas.mathops import MathOpsReq, MathOpsResp

router = APIRouter()


@router.post("/sub")
def sub(add_req: MathOpsReq):
    """Performs subtraction operation.

    Args:
        add_req: An object of MathOpsReq class containing two numbers for subtraction.

    Returns:
        A dictionary containing the result of the subtraction operation.
    """
    ans = subop(add_req.num_1, add_req.num_2)
    return {"ans": ans}


@router.post("/mult")
def sub(add_req: MathOpsReq):
    """Performs multiplication operation.

    Args:
        add_req: An object containing two numbers for multiplication.

    Returns:
        A dictionary containing the result of the multiplication operation.
    """
    ans = multop(add_req.num_1, add_req.num_2)
    return {"ans": ans}
