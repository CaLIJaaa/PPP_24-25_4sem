import os
import eyed3

# Получаем абсолютный путь к директории скрипта
script_dir = os.path.dirname(os.path.abspath(__file__))
# Строим путь к файлу относительно директории скрипта
audio_path = os.path.join(script_dir, "..", "audio_files", "Playboi Carti – BACKD00R.mp3")
audiofile = eyed3.load(audio_path)

if audiofile.tag:
    print(f"Название: {audiofile.tag.title}")
    print(f"Исполнитель: {audiofile.tag.artist}")
    print(f"Альбом: {audiofile.tag.album}")
    print(f"Год: {audiofile.tag.recording_date}")
    print(f"Длительность: {audiofile.info.time_secs} сек")


# Название: BACKD00R
# Исполнитель: Playboi Carti
# Альбом: MUSIC
# Год: 2025-03-14
# Длительность: 190.28 сек