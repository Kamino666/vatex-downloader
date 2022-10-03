import pathlib as plb
import json
from mmcv import VideoReader
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import threading

# 需要检查的文件和视频
video_dir = plb.Path(r"E:\Dataset\VATEX\training set")
video_paths = list(video_dir.glob("*"))


def test_a_video(_p):
    try:
        vr = VideoReader(str(_p))
        _ = vr[3]
        return True, _p
    except Exception as e:
        print(f"[{_p}]Catch {e}")
        return False, _p


unavailable = []
pool = ThreadPoolExecutor(max_workers=4)
results = []
for p in tqdm(video_paths):
    results.append(pool.submit(test_a_video, p))
for res in tqdm(results):
    success, p = res.result()
    if not success:
        unavailable.append(p)

# 写下已经下载但是失效的视频
with open("check.txt", "w+") as f:
    for item in unavailable:
        f.write(f"{item.stem}\n")
