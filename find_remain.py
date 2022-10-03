import pathlib as plb
import json

anno_path = plb.Path(r"./vatex_public_test_english_v1.1.json")
anno_data = json.load(open(anno_path))
video_dir = plb.Path(r".")
video_paths = list(video_dir.glob("*.mp4"))

# 提取数据集中的视频
dataset_ids = [i['videoID'] for i in anno_data]
exist_ids = [i.stem for i in video_paths]
remain_ids = list(set(dataset_ids) - set(exist_ids))
print(f"Total: {len(remain_ids)}")

with open("test_remain.txt", "w+") as f:
    for line in remain_ids:
        f.write(f"{line}\n")
