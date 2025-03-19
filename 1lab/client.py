import socket
import json

class AudioClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
    
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def get_metadata(self):
        if not self.socket:
            if not self.connect():
                return None
        
        try:
            self.socket.send("get_metadata".encode('utf-8'))
            response = self.socket.recv(8192).decode('utf-8')
            return json.loads(response)
        except Exception as e:
            print(f"Ошибка при получении метаданных: {e}")
            return None
    
    def refresh_metadata(self):
        if not self.socket:
            if not self.connect():
                return False
        
        try:
            self.socket.send("refresh".encode('utf-8'))
            response = self.socket.recv(1024).decode('utf-8')
            return json.loads(response)["status"] == "refreshed"
        except Exception as e:
            print(f"Ошибка при обновлении метаданных: {e}")
            return False
    
    def get_audio_list(self):
        if not self.socket:
            if not self.connect():
                return None
    
        try:
            self.socket.send("get_audio_list".encode('utf-8'))
            response = self.socket.recv(8192).decode('utf-8')
            return json.loads(response)
        except Exception as e:
            print(f"Ошибка при получении списка аудио: {e}")
            return None
        
    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

if __name__ == "__main__":
    client = AudioClient()
    try:
        metadata = client.get_audio_list()
        if metadata:
            print("Полученные метаданные:")
            print(json.dumps(metadata, ensure_ascii=False, indent=4))
        else:
            print("Не удалось получить метаданные")
    finally:
        client.close() 