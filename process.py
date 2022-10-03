from tqdm import tqdm
import re
import os
import subprocess
import pathlib as plb
import json


anno_path = plb.Path(r"./vatex_training_v1.0.json")
anno_data = json.load(open(anno_path))
vid2clip = {}
for item in anno_data:
    filename = item['videoID']
    vid = item['videoID'][:11]
    start, end = item['videoID'][12:].split("_")
    vid2clip[vid] = {
        "filename": filename,
        "start": start,
        "end": end
    }

video_dir = plb.Path("videos")
output_video_dir = plb.Path("processed_videos")
videos = list(video_dir.glob("*.mp4"))

for video in tqdm(videos):
    v = vid2clip[video.stem]
    start_int = int(v['start'])
    end_int = int(v['end'])
    video_to_frames_command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-ss", str(start_int),
        "-t", str(end_int - start_int),
        "-vcodec", "h264",
        os.path.join(str(output_video_dir), "_".join([video.stem, v['start'], v['end']]) + ".mp4")
    ]
    print(" ".join(video_to_frames_command))
    with open(os.devnull, "w") as ffmpeg_log:
        subprocess.call(args=video_to_frames_command, stdout=ffmpeg_log, stderr=ffmpeg_log)
