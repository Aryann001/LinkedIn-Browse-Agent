from pydantic import BaseModel
from typing import List

class AgentStartRequest(BaseModel):
    auto_comment: bool = False
    auto_like: bool = False
    max_posts_to_process: int = 5
    cookie_json: str # We now expect the cookie JSON as a string

class AgentStartResponse(BaseModel):
    # This model should ONLY expect the immediate response
    # from the /agent/start endpoint.
    status: str
    message: str