import subprocess
import time
import os
import sys

def run_server():
    server_script = os.path.join(os.path.dirname(__file__), 'server.py')
    return subprocess.Popen([sys.executable, server_script])

def run_client_commands():
    client_script = os.path.join(os.path.dirname(__file__), 'client.py')
    
    # Создаем директорию для аудио файлов, если её нет
    audio_dir = os.path.join(os.path.dirname(__file__), 'audio_files')
    os.makedirs(audio_dir, exist_ok=True)
    
    # Примеры команд для клиента
    commands = [
        ['get'],  # Получить метаданные
        ['refresh'],  # Обновить метаданные
        ['list'],  # Показать список файлов
        ['cut', '--file', '0', '--start', '30', '--end', '50', '--output', 'output123.mp3']  # Обрезать аудио
    ]
    
    for cmd in commands:
        print(f"\nВыполнение команды: {' '.join(cmd)}")
        subprocess.run([sys.executable, client_script] + cmd)
        time.sleep(1)  # Небольшая пауза между командами

def main():
    print("Запуск сервера...")
    server_process = run_server()
    
    # Даем серверу время на запуск
    time.sleep(2)
    
    try:
        print("\nЗапуск клиента и выполнение команд...")
        run_client_commands()
    finally:
        print("\nЗавершение работы сервера...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()

