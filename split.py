import math
import json
import subprocess
from pathlib import Path

SOURCE_DIR = Path("source")
RESULT_DIR = Path("result")
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def get_duration_seconds(file_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(file_path)
    ]
    result = run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error for {file_path.name}:\n{result.stderr}")

    data = json.loads(result.stdout)
    return float(data["format"]["duration"])

def split_file(file_path: Path, segment_length: int, reencode: bool = True):
    duration = get_duration_seconds(file_path)
    parts = math.ceil(duration / segment_length)

    print(f"\nФайл: {file_path.name}")
    print(f"Длительность: {duration:.2f} сек")
    print(f"Сегмент: {segment_length} сек")
    print(f"Частей: {parts}")

    for i in range(parts):
        start = i * segment_length
        output_name = f"{file_path.stem}_part_{i+1:03d}.mp4"
        output_path = RESULT_DIR / output_name

        if reencode:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(start),
                "-i", str(file_path),
                "-t", str(segment_length),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                str(output_path)
            ]
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(start),
                "-i", str(file_path),
                "-t", str(segment_length),
                "-c", "copy",
                str(output_path)
            ]

        print(f"[{i+1}/{parts}] {output_name}")
        result = run(cmd)

        if result.returncode != 0:
            print("Ошибка FFmpeg:")
            print(result.stderr)
            break

def main():
    SOURCE_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)

    video_files = sorted(
        [p for p in SOURCE_DIR.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS]
    )

    if not video_files:
        print("В папке source нет видеофайлов.")
        print("Поддерживаемые форматы:", ", ".join(sorted(VIDEO_EXTS)))
        return

    try:
        segment_length = int(input("Введите длину сегмента в секундах: ").strip())
        if segment_length <= 0:
            print("Длина сегмента должна быть больше 0.")
            return
    except ValueError:
        print("Нужно ввести целое число.")
        return

    mode = input("Точная нарезка с перекодированием? (y/n): ").strip().lower()
    reencode = mode == "y"

    print(f"\nНайдено файлов: {len(video_files)}")
    print(f"Источник: {SOURCE_DIR.resolve()}")
    print(f"Результат: {RESULT_DIR.resolve()}")

    for file_path in video_files:
        try:
            split_file(file_path, segment_length, reencode=reencode)
        except Exception as e:
            print(f"\nОшибка при обработке {file_path.name}: {e}")

    print("\nГотово.")

if __name__ == "__main__":
    main()