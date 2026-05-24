import subprocess
from pathlib import Path

SOURCE_DIR = Path("result")
OUTPUT_DIR = Path("final")
OVERLAY_FILE = Path("overlay.mp4")

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

TARGET_W = 1080
TARGET_H = 1920

CHROMA_COLOR = "0xFF3EAA"
SIMILARITY = "0.09"
BLEND = "0.00"

PRESET = "fast"
CRF = "18"
AUDIO_BITRATE = "192k"
OVERLAY_PAD_SECONDS = "0.5"

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def build_filter():
    return (
        f"[0:v]"
        f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_W}:{TARGET_H}:(iw-{TARGET_W})/2:(ih-{TARGET_H})/2"
        f"[bg];"
        f"[1:v]"
        f"colorkey={CHROMA_COLOR}:{SIMILARITY}:{BLEND},"
        f"tpad=stop_mode=clone:stop_duration={OVERLAY_PAD_SECONDS},"
        f"format=rgba,split[fg][fg2];"
        f"[fg]alphaextract,erosion=1,boxblur=1[mask];"
        f"[fg2][mask]alphamerge[ov];"
        f"[bg][ov]overlay=0:0[outv]"
    )

def process_file(background_file: Path):
    output_name = f"{background_file.stem}_final.mp4"
    output_path = OUTPUT_DIR / output_name

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(background_file),
        "-i", str(OVERLAY_FILE),
        "-filter_complex", build_filter(),
        "-map", "[outv]",
        "-map", "1:a?",
        "-af", f"apad=pad_dur={OVERLAY_PAD_SECONDS}",
        "-c:v", "libx264",
        "-preset", PRESET,
        "-crf", CRF,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-shortest",
        str(output_path)
    ]

    print(f"Обработка: {background_file.name} -> {output_name}")
    result = run(cmd)

    if result.returncode != 0:
        print(f"\nОшибка при обработке {background_file.name}:")
        print(result.stderr)
        return False
    return True

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not OVERLAY_FILE.exists():
        print(f"Не найден файл: {OVERLAY_FILE}")
        return

    if not SOURCE_DIR.exists():
        print("Не найдена папка result")
        return

    files = sorted([p for p in SOURCE_DIR.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS])

    if not files:
        print("В папке result нет видеофайлов.")
        return

    print(f"Найдено файлов: {len(files)}")

    ok = 0
    fail = 0

    for f in files:
        if process_file(f):
            ok += 1
        else:
            fail += 1

    print("\nГотово.")
    print(f"Успешно: {ok}")
    print(f"С ошибкой: {fail}")

if __name__ == "__main__":
    main()