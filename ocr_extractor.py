import json
import os
import random
import shutil
import subprocess
from pathlib import Path

from paddleocr import PaddleOCR
from tqdm import tqdm


# Paddleocr目前支持的多语言语种可以通过修改lang参数进行切换
# 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
# ocr = PaddleOCR(use_angle_cls=True, lang="en")  # need to run only once to download and load model into memory
# img_path = '123.jpg'
# result = ocr.ocr(img_path, det=True, cls=True)
# for line in result:
#     print(line)


def reencode_video_with_diff_fps(video_path: str, tmp_path: str, extraction_fps: float):
    # create tmp dir if doesn't exist
    os.makedirs(tmp_path, exist_ok=True)
    new_dir = Path(tmp_path) / f'{Path(video_path).stem}'
    new_dir.mkdir()
    pattern = new_dir / '%06d.jpg'

    cmd = f'ffmpeg -hide_banner -loglevel panic '
    cmd += f'-y -i {video_path} -filter:v fps=fps={extraction_fps} {pattern}'
    subprocess.call(cmd.split())

    return new_dir


class OCRExtractor:
    def __init__(self, input_dir, output_dir, fps=.5, lang="en", tmp_path="./tmp", use_gpu=True):
        self.fps = fps
        self.video_paths = list(Path(input_dir).glob("*"))
        random.shuffle(self.video_paths)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        # self.exist_outputs = set([i.stem for i in self.output_dir.glob("*.json")])
        self.model = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=use_gpu, show_log=False)
        self.tmp_path = tmp_path

    def run(self):
        for path in tqdm(self.video_paths):
            # check if already exists
            tgt_path = self.output_dir / f"{path.stem}.json"
            if tgt_path.exists():
                print(f"Skip: {tgt_path}")
                continue

            # extract video frames with different fps
            new_frames_dir = reencode_video_with_diff_fps(path, self.tmp_path, extraction_fps=self.fps)

            # load and inference
            img_paths = sorted(list(Path(new_frames_dir).glob("*.jpg")))
            results = []
            for img_p in img_paths:
                res = self.model.ocr(str(img_p), det=True, cls=True)[0]
                results += [i[1] for i in res]
            shutil.rmtree(new_frames_dir)  # delete tmp files

            # write data
            with open(tgt_path, "w+") as f:
                json.dump(results, f)


if __name__ == '__main__':
    extractor = OCRExtractor(
        input_dir="videos/validation",
        output_dir="ocr",
        use_gpu=False
    )
    extractor.run()
