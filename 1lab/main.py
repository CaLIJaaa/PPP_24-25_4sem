import subprocess
import time
import os
import sys

def run_server():
    server_script = os.path.join(os.path.dirname(__file__), 'server.py')
    return subprocess.Popen([sys.executable, server_script])

def run_client_commands():
    client_script = os.path.join(os.path.dirname(__file__), 'client.py')
    
    audio_dir = os.path.join(os.path.dirname(__file__), 'audio_files')
    os.makedirs(audio_dir, exist_ok=True)
    
    commands = [
        ['get'], 
        ['refresh'], 
        ['list'], 
        ['cut', '--file', '0', '--start', '30', '--end', '50', '--output', 'output123.mp3'] 
    ]
    
    for cmd in commands:
        print(f"\nВыполнение команды: {' '.join(cmd)}")
        subprocess.run([sys.executable, client_script] + cmd)
        time.sleep(1) 

def main():
    print("Запуск сервера...")
    server_process = run_server()
    
    time.sleep(2)
    
    try:
        print("\nЗапуск клиента и выполнение команд...")
        run_client_commands()
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        print("\nЗавершение работы сервера...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()

