import socket
import json
import argparse
import os
import logging
import tempfile
import shutil

class AudioClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        log_dir = os.path.join(script_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        self.output_dir = os.path.join(script_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.temp_dir = os.path.join(script_dir, 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'client_log.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Клиент инициализирован")
        self.logger.info(f"Директория для выходных файлов: {self.output_dir}")
        self.logger.info(f"Директория для временных файлов: {self.temp_dir}")
    
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.logger.info(f"Подключение к {self.host}:{self.port}")
            self.socket.connect((self.host, self.port))
            self.logger.info("Подключение успешно установлено")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка подключения: {str(e)}", exc_info=True)
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

    def get_part_of_audio(self, file_index, start_time, end_time, output_path):
        if not self.socket:
            if not self.connect():
                return False
        
        temp_fd = None
        temp_path = None
        
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            command = {
                "command": "get_part_of_audio",
                "file_index": int(file_index),
                "start_time": start_time,
                "end_time": end_time
            }
            
            self.logger.info(f"Отправка запроса на получение части аудио: {command}")
            self.socket.send(json.dumps(command).encode('utf-8'))
            
            self.logger.debug("Ожидание размера данных")
            size_data = self.socket.recv(8)
            if not size_data:
                self.logger.error("Не удалось получить размер данных")
                return False
            
            try:
                error_response = json.loads(size_data.decode('utf-8'))
                if "error" in error_response:
                    self.logger.error(f"Получена ошибка от сервера: {error_response['error']}")
                    return False
            except:
                pass
                
            total_size = int.from_bytes(size_data, byteorder='big')
            self.logger.info(f"Ожидаемый размер данных: {total_size} байт")
            
            temp_fd, temp_path = tempfile.mkstemp(dir=self.temp_dir, suffix='.mp3.temp')
            self.logger.debug(f"Создан временный файл: {temp_path}")
            
            received_data = 0
            self.logger.debug("Начало получения аудио данных")
            
            with os.fdopen(temp_fd, 'wb') as temp_file:
                while received_data < total_size:
                    chunk_size = min(4096, total_size - received_data)
                    self.logger.debug(f"Получение чанка размером {chunk_size} байт")
                    chunk = self.socket.recv(chunk_size)
                    if not chunk:
                        self.logger.error("Соединение прервано при получении данных")
                        break
                    temp_file.write(chunk)
                    received_data += len(chunk)
                    self.logger.debug(f"Получено {received_data} из {total_size} байт")
            
            if received_data == total_size:
                shutil.move(temp_path, output_path)
                self.logger.info(f"Аудио файл успешно сохранен в {output_path}")
                return True
            else:
                self.logger.error(f"Получено неверное количество данных: {received_data} из {total_size}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка при получении части аудио: {str(e)}", exc_info=True)
            return False
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    self.logger.debug(f"Временный файл удален: {temp_path}")
                except Exception as e:
                    self.logger.error(f"Ошибка при удалении временного файла: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Клиент для получения метаданных аудио файлов')


    parser.add_argument('command', choices=['get', 'refresh', 'cut', 'list'], 
                       help='Команда: get - получить метаданные, refresh - обновить метаданные, cut - получить часть аудио, list - показать список файлов')
    parser.add_argument('--file', type=int, help='Индекс файла для обрезки (начиная с 0)')
    parser.add_argument('--start', type=float, help='Начальное время в секундах')
    parser.add_argument('--end', type=float, help='Конечное время в секундах')
    parser.add_argument('--output', help='Имя выходного файла (будет сохранен в директорию output)')
    
    args = parser.parse_args()
    
    client = AudioClient(host='localhost', port=12345)
    try:
        if args.command == 'get':
            metadata = client.get_metadata()
            if metadata:
                print("Полученные метаданные:")
                print(json.dumps(metadata, ensure_ascii=False, indent=4))
            else:
                print("Не удалось получить метаданные")
        elif args.command == 'refresh':
            if client.refresh_metadata():
                print("Метаданные успешно обновлены")
            else:
                print("Не удалось обновить метаданные")
        elif args.command == 'list':
            audio_list = client.get_audio_list()
            if audio_list:
                print("Список доступных аудио файлов:")
                for i, name in enumerate(audio_list):
                    print(f"{i}: {name}")
            else:
                print("Не удалось получить список аудио файлов")
        elif args.command == 'cut':
            if not all([args.file is not None, args.start, args.end, args.output]):
                print("Необходимо указать --file (индекс), --start, --end и --output для команды cut")
                exit(1)
            
            output_path = os.path.join(client.output_dir, args.output)
            
            if client.get_part_of_audio(args.file, args.start, args.end, output_path):
                print(f"Аудио успешно обрезано и сохранено в {output_path}")
            else:
                print("Не удалось получить часть аудио")
    finally:
        client.close() 