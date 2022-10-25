"""
修复硬盘上出现的命名失误
"""
import os
import pathlib as plb
from tqdm import tqdm

video_dir = plb.Path(r"E:\Dataset\VATEX\validation set")
video_paths = list(video_dir.glob("*"))

for src in tqdm(video_paths):
    tgt_file_name = src.name[:19] + "0" + src.name[19:]
    tgt = src.parent / tgt_file_name
    os.rename(str(src), str(tgt))
    # print(str(src), str(tgt))


