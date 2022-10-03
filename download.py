from concurrent.futures import ThreadPoolExecutor
import subprocess
from tqdm import tqdm
import json
import pathlib as plb


def get_a_video(video_id):
    url = "https://www.youtube.com/watch?v=" + video_id
    result = subprocess.run(args=["youtube-dl",
                                  "-f", "best[ext=mp4]/best",
                                  "-o", "videos/%(id)s.%(ext)s",
                                  url],
                            capture_output=True)
    err_str = result.stderr.decode('utf-8')
    if "ERROR: Private video" in err_str:
        black_list.append(video_id)
    elif "ERROR: Video unavailable" in err_str:
        black_list.append(video_id)
    elif "ERROR: Sign in to confirm your age" in err_str:
        black_list.append(video_id)
    elif "ERROR: This video has been removed" in err_str:
        black_list.append(video_id)
    elif "ERROR: unable to download video data: HTTP Error 403: Forbidden" in err_str:
        print("save to redownload.txt", video_id, err_str)
        redownload_list.append(video_id)
    elif "ERROR" in err_str:
        print(video_id, err_str)
    return result.returncode


# 读入旧黑名单
old_black_list_txt = plb.Path("blacklist.txt")  # 这里写黑名单
if old_black_list_txt.is_file() and old_black_list_txt.exists():
    with open(str(old_black_list_txt)) as f:
        old_black_list = f.read().split("\n")
else:
    old_black_list = []
black_list = []

# 由于下载太过频繁而无法下载的视频
redownload_list = []

check_txt = plb.Path("test_remain.txt")  # 这里写输入
# check_txt = plb.Path("redownload.txt")  # 这里写输入
with open(check_txt) as f:
    data = f.read().split("\n")[:-1]
# data = ["R0M0xbeZR0E"]

pool = ThreadPoolExecutor(max_workers=6)
results = []
for item in data[100:150]:
# for item in data:
    vid = item[:11]
    if vid in old_black_list:
        continue
    results.append(pool.submit(get_a_video, vid))
for r in tqdm(results):
    r.result()

# 更新黑名单
if len(black_list) != 0:
    with open(old_black_list_txt, 'a') as f:
        for line in black_list:
            f.write(f"{line}\n")
# 保存再下载的视频列表
if len(black_list) != 0:
    with open("redownload.txt", "w+") as f:
        for line in redownload_list:
            f.write(f"{line}\n")
