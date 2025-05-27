from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, Literal

class BaseRequest(BaseModel):
    key: str

class EncodeRestRequest(BaseRequest):
    text: str

class EncodeRestResponse(BaseModel):
    task_id: str
    message: str = "Encode task started"

class DecodeRestRequest(BaseRequest):
    encoded_data: str
    huffman_codes: Dict[str, str]
    padding: int

class DecodeRestResponse(BaseModel):
    task_id: str
    message: str = "Decode task started"

class WebSocketMessageBase(BaseModel):
    task_id: str
    operation: str # "encode" или "decode"

class TaskStartedMessage(WebSocketMessageBase):
    status: Literal["STARTED"] = "STARTED"

class TaskProgressMessage(WebSocketMessageBase):
    status: Literal["PROGRESS"] = "PROGRESS"
    progress: int # 0-100

class EncodeResultMessage(BaseModel):
    encoded_data: str
    huffman_codes: Dict[str, str]
    padding: int

class DecodeResultMessage(BaseModel):
    decoded_text: str

class TaskCompletedMessage(WebSocketMessageBase):
    status: Literal["COMPLETED"] = "COMPLETED"
    result: Any

class TaskFailedMessage(WebSocketMessageBase):
    status: Literal["FAILED"] = "FAILED"
    error: str 