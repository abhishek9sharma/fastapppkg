from datetime import datetime

from pydantic import BaseModel


class MathOpsReq(BaseModel):
    num_1: float
    num_2: float


class MathOpsResp(BaseModel):
    answer: float
