import asyncio
from app.celery.celery_app import celery_app
from app.services.encryption_service import perform_encode, perform_decode
from app.schemas.encryption_schemas import (
    TaskStartedMessage, TaskProgressMessage, TaskCompletedMessage, TaskFailedMessage,
    EncodeResultMessage, DecodeResultMessage
)
import uuid
import time
import httpx

FASTAPI_NOTIFICATION_URL = "http://127.0.0.1:8000/encryption/internal/notify_client"

def send_notification_to_fastapi(task_id: str, client_id: str, message_data: dict):
    payload = {
        "client_id": client_id,
        "task_id": task_id,
        "message_data": message_data
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(FASTAPI_NOTIFICATION_URL, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"HTTP StatusError sending notification for task {task_id} to client {client_id}: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"HTTP RequestError sending notification for task {task_id} to client {client_id}: {e}")
    except Exception as e:
        print(f"Unexpected error sending notification for task {task_id} to client {client_id}: {e}")

@celery_app.task(bind=True)
def encode_task(self, text: str, key: str, client_id: str):
    task_id = str(self.request.id) if self.request.id else str(uuid.uuid4())
    operation = "encode"
    
    print(f"[Celery Worker] Starting encode task {task_id} for client {client_id}")
    start_msg = TaskStartedMessage(task_id=task_id, operation=operation).model_dump()
    send_notification_to_fastapi(task_id, client_id, start_msg)

    def progress_callback(current_task_id, op, progress_percentage):
        progress_msg = TaskProgressMessage(
            task_id=current_task_id, 
            operation=op, 
            progress=progress_percentage
        ).model_dump()
        send_notification_to_fastapi(current_task_id, client_id, progress_msg)
        if progress_percentage < 100 : time.sleep(0.05)

    try:
        time.sleep(0.1)
        result_data = perform_encode(text, key, task_id, progress_callback)
        
        result_for_schema = {
            "encoded_data": result_data.get("encoded_data"),
            "huffman_codes": result_data.get("huffman_codes"),
            "padding": result_data.get("padding")
        }
        completed_result = EncodeResultMessage(**result_for_schema)
        completed_msg = TaskCompletedMessage(
            task_id=task_id, 
            operation=operation, 
            result=completed_result
        ).model_dump()
        send_notification_to_fastapi(task_id, client_id, completed_msg)
        print(f"[Celery Worker] Encode task {task_id} completed.")
        return completed_msg
    except Exception as e:
        print(f"[Celery Worker] Error in encode_task {task_id}: {e}")
        error_msg = TaskFailedMessage(task_id=task_id, operation=operation, error=str(e)).model_dump()
        send_notification_to_fastapi(task_id, client_id, error_msg)
        raise

@celery_app.task(bind=True)
def decode_task(self, encoded_data: str, key: str, huffman_codes: dict, padding: int, client_id: str):
    task_id = str(self.request.id) if self.request.id else str(uuid.uuid4())
    operation = "decode"

    print(f"[Celery Worker] Starting decode task {task_id} for client {client_id}")
    start_msg = TaskStartedMessage(task_id=task_id, operation=operation).model_dump()
    send_notification_to_fastapi(task_id, client_id, start_msg)

    def progress_callback(current_task_id, op, progress_percentage):
        progress_msg = TaskProgressMessage(
            task_id=current_task_id, 
            operation=op, 
            progress=progress_percentage
        ).model_dump()
        send_notification_to_fastapi(current_task_id, client_id, progress_msg)
        if progress_percentage < 100 : time.sleep(0.05)

    try:
        time.sleep(0.1)
        result_data = perform_decode(encoded_data, key, huffman_codes, padding, task_id, progress_callback)

        completed_result = DecodeResultMessage(**result_data)
        completed_msg = TaskCompletedMessage(
            task_id=task_id, 
            operation=operation, 
            result=completed_result
        ).model_dump()
        send_notification_to_fastapi(task_id, client_id, completed_msg)
        print(f"[Celery Worker] Decode task {task_id} completed.")
        return completed_msg
    except Exception as e:
        print(f"[Celery Worker] Error in decode_task {task_id}: {e}")
        error_msg = TaskFailedMessage(task_id=task_id, operation=operation, error=str(e)).model_dump()
        send_notification_to_fastapi(task_id, client_id, error_msg)
        raise