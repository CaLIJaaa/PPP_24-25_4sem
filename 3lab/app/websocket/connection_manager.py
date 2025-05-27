from fastapi import WebSocket
from typing import Dict, List, DefaultDict
from collections import defaultdict
import json

class ConnectionManager:
    def __init__(self):
        # Храним активные соединения: client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Храним задачи, на которые подписан клиент: client_id -> List[task_id]
        self.client_subscriptions: DefaultDict[str, List[str]] = defaultdict(list)
        # Храним клиентов, подписанных на задачу: task_id -> List[client_id]
        self.task_subscribers: DefaultDict[str, List[str]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            # Перед удалением соединения, отписываем клиента от всех его задач
            tasks_to_cleanup = list(self.client_subscriptions.get(client_id, []))
            for task_id in tasks_to_cleanup:
                self.unsubscribe(client_id, task_id)
            del self.active_connections[client_id]
            if client_id in self.client_subscriptions:
                 del self.client_subscriptions[client_id]
            print(f"Client {client_id} disconnected. Total clients: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"Error sending text to client {client_id}: {e}. Disconnecting.")
                self.disconnect(client_id)

    async def send_personal_message_json(self, data: dict, client_id: str, task_id_for_subscription: str = None):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            # Если это сообщение о старте задачи, подписываем клиента на эту задачу
            if task_id_for_subscription and data.get("status") == "STARTED":
                self.subscribe(client_id, task_id_for_subscription)
            
            # Если это сообщение о завершении или ошибке, отписываем клиента от задачи
            if task_id_for_subscription and data.get("status") in ["COMPLETED", "FAILED"]:
                self.unsubscribe(client_id, task_id_for_subscription)
                
            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"Error sending json to client {client_id}: {e}. Disconnecting.")
                self.disconnect(client_id)
    
    def subscribe(self, client_id: str, task_id: str):
        if client_id not in self.client_subscriptions[client_id]:
            self.client_subscriptions[client_id].append(task_id)
        if client_id not in self.task_subscribers[task_id]:
            self.task_subscribers[task_id].append(client_id)
        print(f"Client {client_id} subscribed to task {task_id}")

    def unsubscribe(self, client_id: str, task_id: str):
        if task_id in self.client_subscriptions.get(client_id, []):
            self.client_subscriptions[client_id].remove(task_id)
            if not self.client_subscriptions[client_id]: # если список подписок пуст
                del self.client_subscriptions[client_id]

        if client_id in self.task_subscribers.get(task_id, []):
            self.task_subscribers[task_id].remove(client_id)
            if not self.task_subscribers[task_id]: # если список подписчиков пуст
                del self.task_subscribers[task_id]
        print(f"Client {client_id} unsubscribed from task {task_id}")

    async def broadcast_to_task_subscribers(self, task_id: str, message_data: dict):
        # Эта функция не используется напрямую Celery задачами в текущей реализации,
        # так как Celery задачи отправляют сообщение конкретному client_id, который инициировал задачу.
        # Но она может быть полезна для других сценариев.
        subscribers = list(self.task_subscribers.get(task_id, [])) # Копируем список для безопасной итерации
        print(f"Broadcasting to subscribers of task {task_id}: {subscribers}")
        for client_id in subscribers:
            await self.send_personal_message_json(message_data, client_id)

manager = ConnectionManager() 