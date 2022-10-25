import pathlib as plb
import json

anno_path = plb.Path(r"./vatex_validation_v1.0.json")
anno_data = json.load(open(anno_path))
video_dir = plb.Path(r"E:\Dataset\VATEX\validation set")
video_paths = list(video_dir.glob("*.mp4"))

# 提取数据集中的视频
dataset_ids = [i['videoID'] for i in anno_data]
exist_ids = [i.stem for i in video_paths]
remain_ids = list(set(dataset_ids) - set(exist_ids))
print(f"Total: {len(remain_ids)}")

with open("valid_remain.txt", "w+") as f:
    for line in remain_ids:
        f.write(f"{line}\n")
