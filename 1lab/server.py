import os
import json
import eyed3
import socket
import threading
from pydub import AudioSegment
import io
import logging

class AudioServer:
    def __init__(self, host='localhost', port=12345, audio_dir='audio_files'):
        self.host = host
        self.port = port
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.audio_dir = os.path.join(script_dir, audio_dir)
        self.audio_metadata = {}
        self.server_socket = None
        self.running = False
        
        log_dir = os.path.join(script_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'server_log.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Сервер инициализирован")
        self.logger.info(f"Директория с аудио: {self.audio_dir}")
        self.logger.info(f"Директория для логов: {log_dir}")
            
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
    
    def get_audio_segment(self, file_index, start_time, end_time):
        try:
            self.logger.info(f"Запрос на обрезку файла: индекс={file_index}, start={start_time}, end={end_time}")
            files = list(self.audio_metadata.keys())
            if file_index >= len(files):
                self.logger.error(f"Индекс файла {file_index} вне диапазона (всего файлов: {len(files)})")
                return None
                
            file_path = os.path.join(self.audio_dir, files[file_index])
            self.logger.debug(f"Загрузка файла: {file_path}")
            
            audio = AudioSegment.from_mp3(file_path)
            self.logger.debug(f"Файл загружен, длительность: {len(audio)/1000} сек")
            
            start_ms = int(float(start_time) * 1000)
            end_ms = int(float(end_time) * 1000)
            
            self.logger.debug(f"Обрезка аудио: {start_ms}мс - {end_ms}мс")
            audio_segment = audio[start_ms:end_ms]
            
            buffer = io.BytesIO()
            self.logger.debug("Экспорт обрезанного аудио")
            audio_segment.export(buffer, format='mp3')
            
            result = buffer.getvalue()
            self.logger.info(f"Обрезка завершена, размер результата: {len(result)} байт")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка при обработке аудио: {str(e)}", exc_info=True)
            return None

    def handle_client(self, client_socket):
        try:
            client_address = client_socket.getpeername()
            self.logger.info(f"Новое подключение от {client_address}")
            
            while True:
                command = client_socket.recv(1024).decode('utf-8')
                if not command:
                    break
                
                self.logger.debug(f"Получена команда от {client_address}: {command}")
                
                try:
                    command_data = json.loads(command)
                    command_type = command_data.get('command')
                except json.JSONDecodeError:
                    command_type = command

                if command_type == "get_metadata":
                    self.logger.debug("Отправка метаданных")
                    response = json.dumps(self.audio_metadata, ensure_ascii=False)
                    client_socket.send(response.encode('utf-8'))
                elif command_type == "refresh":
                    self.logger.debug("Обновление метаданных")
                    self.scan_audio_files()
                    response = json.dumps({"status": "refreshed"})
                    client_socket.send(response.encode('utf-8'))
                elif command_type == "get_audio_list":
                    self.logger.debug("Отправка списка аудио")
                    response = json.dumps([self.audio_metadata[title]['name'] for title in self.audio_metadata.keys()], ensure_ascii=False)
                    client_socket.send(response.encode('utf-8'))
                elif command_type == "get_part_of_audio":
                    file_index = command_data.get('file_index')
                    start_time = command_data.get('start_time')
                    end_time = command_data.get('end_time')
                    
                    self.logger.info(f"Запрос на получение части аудио: файл {file_index}, {start_time}-{end_time} сек")
                    
                    if not all([file_index is not None, start_time, end_time]):
                        error_msg = "Не указаны все необходимые параметры"
                        self.logger.error(error_msg)
                        response = json.dumps({"error": error_msg})
                        client_socket.send(response.encode('utf-8'))
                        continue
                    
                    audio_data = self.get_audio_segment(file_index, start_time, end_time)
                    if audio_data:
                        self.logger.debug(f"Отправка аудио данных размером {len(audio_data)} байт")
                        size_data = len(audio_data).to_bytes(8, byteorder='big')
                        client_socket.send(size_data)
                        client_socket.sendall(audio_data)
                        self.logger.info("Аудио данные успешно отправлены")
                    else:
                        error_msg = "Ошибка при обработке аудио"
                        self.logger.error(error_msg)
                        response = json.dumps({"error": error_msg})
                        client_socket.send(response.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Ошибка при обработке клиента: {str(e)}", exc_info=True)
        finally:
            self.logger.info(f"Закрытие соединения с {client_address}")
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