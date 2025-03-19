import os
import json
import eyed3
import socket
import threading

class AudioServer:
    def __init__(self, host='localhost', port=12345, audio_dir='audio_files'):
        self.host = host
        self.port = port
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.audio_dir = os.path.join(script_dir, audio_dir)
        self.audio_metadata = {}
        self.server_socket = None
        self.running = False
            
        self.scan_audio_files()
        
    def scan_audio_files(self):
        self.audio_metadata = {}
        for filename in os.listdir(self.audio_dir):
            if filename.endswith(('.mp3', '.wav')):
                file_path = os.path.join(self.audio_dir, filename)
                try:
                    audiofile = eyed3.load(file_path)
                    self.audio_metadata[filename] = {
                        'name': audiofile.tag.title,
                        'artist': audiofile.tag.artist,
                        'album': audiofile.tag.album,
                        'year': str(audiofile.tag.recording_date) if audiofile.tag.recording_date else None,
                        'duration': audiofile.info.time_secs
                    }
                except Exception as e:
                    pass
        
        with open('audio_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(self.audio_metadata, f, ensure_ascii=False, indent=4)
            
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Сервер запущен на {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
            except Exception as e:
                print(f"Ошибка при подключении клиента: {e}")
    
    def handle_client(self, client_socket):
        try:
            while True:
                command = client_socket.recv(1024).decode('utf-8')
                if not command:
                    break
                
                if command == "get_metadata":
                    response = json.dumps(self.audio_metadata, ensure_ascii=False)
                    client_socket.send(response.encode('utf-8'))
                elif command == "refresh":
                    self.scan_audio_files()
                    response = json.dumps({"status": "refreshed"})
                    client_socket.send(response.encode('utf-8'))
                elif command == "get_audio_list":
                    response = json.dumps([self.audio_metadata[title]['name'] for title in self.audio_metadata.keys()], ensure_ascii=False)
                    client_socket.send(response.encode('utf-8'))
        except Exception as e:
            print(f"Ошибка при обработке клиента: {e}")
        finally:
            client_socket.close()
    
    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    server = AudioServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nЗавершение работы сервера...")
        server.stop()