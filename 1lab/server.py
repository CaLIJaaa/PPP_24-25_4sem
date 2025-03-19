import os
import json
import eyed3

class AudioServer:
    def __init__(self, host='localhost', port=12345, audio_dir='audio_files'):
        self.host = host
        self.port = port
        # Получаем абсолютный путь к директории скрипта
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Формируем путь к директории с аудио файлами
        self.audio_dir = os.path.join(script_dir, audio_dir)
        self.audio_metadata = {}
            
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
            
if __name__ == "__main__":
    server = AudioServer()
    print(server.audio_metadata)