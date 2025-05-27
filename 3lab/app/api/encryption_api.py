from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Path, HTTPException
from app.schemas.encryption_schemas import (
    EncodeRestRequest, EncodeRestResponse, 
    DecodeRestRequest, DecodeRestResponse
)
from app.celery.tasks import encode_task, decode_task
from app.websocket.connection_manager import manager
import uuid
from pydantic import BaseModel
from typing import Any

router = APIRouter()

class NotificationPayload(BaseModel):
    client_id: str
    task_id: str
    message_data: dict[str, Any]

@router.post("/internal/notify_client")
async def notify_client_endpoint(payload: NotificationPayload):
    try:
        await manager.send_personal_message_json(
            data=payload.message_data,
            client_id=payload.client_id,
            task_id_for_subscription=payload.task_id 
        )
        return {"status": "notification sent to client", "client_id": payload.client_id, "task_id": payload.task_id}
    except Exception as e:
        print(f"Error in /internal/notify_client for client {payload.client_id}, task {payload.task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send WebSocket notification to client {payload.client_id}: {str(e)}")

@router.post("/encode/{client_id}", response_model=EncodeRestResponse)
async def trigger_encode(request: EncodeRestRequest, client_id: str = Path(..., description="Уникальный ID клиента для WebSocket")):
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id is required as a path parameter for WebSocket notifications.")
    
    celery_task = encode_task.delay(request.text, request.key, client_id)
    return EncodeRestResponse(task_id=celery_task.id, message=f"Encode task {celery_task.id} started for client {client_id}")

@router.post("/decode/{client_id}", response_model=DecodeRestResponse)
async def trigger_decode(request: DecodeRestRequest, client_id: str = Path(..., description="Уникальный ID клиента для WebSocket")):
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id is required as a path parameter for WebSocket notifications.")

    celery_task = decode_task.delay(
        request.encoded_data, 
        request.key, 
        request.huffman_codes, 
        request.padding,
        client_id
    )
    return DecodeRestResponse(task_id=celery_task.id, message=f"Decode task {celery_task.id} started for client {client_id}")

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text() 
            pass 
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"Client {client_id} disconnected from WebSocket.")
    except Exception as e:
        print(f"Error in WebSocket for client {client_id}: {e}")
        manager.disconnect(client_id)