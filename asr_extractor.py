from pathlib import Path
import subprocess

# "paddlespeech asr --lang zh --input zh.wav"

# 启动服务端
# paddlespeech_server start --config_file ./asr_conf/en.yaml


# asr = ASRExecutor()
# result = asr(audio_file=Path("en.wav"))
# print(result)
# 我认为跑步最重要的就是给我带来了身体健康
# result = subprocess.run(args=[
#     'paddlespeech', 'asr', '--model', 'transformer_librispeech',
#     '--lang', 'en', '--input', 'en.wav'
# ], stdout=subprocess.PIPE)
# output = result.stdout.decode('utf-8').split("\r\n")[-1].replace('\x1b[0m', '')

from paddlespeech.server.bin.paddlespeech_client import ASRClientExecutor
import os
import random
from tqdm import tqdm


def extract_audio_by_ffmpeg(video_path: str, tmp_path: str, sample_rate=16000):
    # create tmp dir if doesn't exist
    os.makedirs(tmp_path, exist_ok=True)
    new_path = Path(tmp_path) / f"{Path(video_path).stem}.wav"

    subprocess.call(args=[
        'ffmpeg', '-hide_banner', '-loglevel', 'panic', '-y',
        '-i', video_path,
        '-ar', str(sample_rate),  # 采样率
        '-vn',  # 不要视频
        new_path,
    ])

    return new_path


class ASRExtractor:
    def __init__(self, input_dir, output_dir, lang="en", tmp_path="./tmp"):
        self.video_paths = list(Path(input_dir).glob("*.mp4"))
        random.shuffle(self.video_paths)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.model = ASRClientExecutor()
        self.lang = lang
        self.tmp_path = tmp_path

    def run(self):
        for path in tqdm(self.video_paths):
            # check if already exists
            tgt_path = self.output_dir / f"{path.stem}.txt"
            if tgt_path.exists():
                print(f"Skip: {tgt_path}")
                continue
            else:
                f = open(tgt_path, "w+")

            # extract wav audio
            wav_path = extract_audio_by_ffmpeg(path, self.tmp_path)

            # inference
            res = self.model(input=str(wav_path), server_ip="127.0.0.1", port=8090, sample_rate=16000,
                             lang=self.lang, audio_format="wav")

            # delete
            os.remove(wav_path)

            # write data
            f.write(res)


if __name__ == '__main__':
    extractor = ASRExtractor(
        input_dir="videos/validation",
        output_dir="asr",
    )
    extractor.run()
