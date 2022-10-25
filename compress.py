import subprocess
from pathlib import Path
from tqdm import tqdm


"""
压缩分辨率
ffmpeg -i input.mp4 -vf scale=320:240 -y output.mp4
"""
OUTPUT_DIR = Path("validation_low_res")
INPUT_DIR = Path("processed_videos")

OUTPUT_DIR.mkdir(exist_ok=True)
for vid in tqdm(list(INPUT_DIR.glob("*.mp4"))):
    result = subprocess.run([
        "ffmpeg",
        "-i", str(vid),
        "-vf", "scale=320:240",
        "-y", str(OUTPUT_DIR / vid.name)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        print(f"vid: {vid.stem} code: {result.returncode}")

