import sqlite3
import json
import pathlib as plb
from yt_dlp import YoutubeDL, DownloadError
from threading import Thread, Lock, current_thread
from queue import Queue, Empty
import os
import time

DATABASE = "vatex-download.db"


def init_database(anno_list: list):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # 新建表
    cursor.execute(
        "CREATE TABLE vatex (vid varchar(25) primary key,"
        " status varchar(20), split varchar(10),"
        " details varchar(100), asr integer)"
    )
    # 读取vatex数据集
    for anno in anno_list:
        split, path = anno['split'], anno['path']
        with open(path) as f:
            data = json.load(f)
        print(f"读取{split}中，共包含{len(data)}项")
        for item in data:
            vid = item['videoID']
            cursor.execute(
                f"INSERT INTO vatex (vid, status, split) VALUES ('{vid}', 'waiting', '{split}')"
            )
    cursor.close()
    conn.commit()
    conn.close()


def dump_exist_videos_to_database(from_dir=None):
    vids = []
    for i in plb.Path(from_dir).glob("*.mp4"):
        if i.stat().st_size < 1000:
            continue
        vids.append(i.stem)
    print(f"获取到{len(vids)}条视频")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for v in vids:
        cursor.execute(f"UPDATE vatex set status = 'successful' where vid = '{v}'")
    cursor.close()
    conn.commit()
    conn.close()


def write_result(full_vid, status, details=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    if details is None:
        cursor.execute(f"UPDATE vatex set status='{status}' where vid = '{full_vid}'")
    else:
        cursor.execute(f"UPDATE vatex set status='{status}',details=? where vid = '{full_vid}'", (details,))
    cursor.close()
    conn.commit()
    conn.close()


def load_black_list_to_database():
    with open("vatex_training_v1.0.json") as f:
        train = json.load(f)
    with open("vatex_validation_v1.0.json") as f:
        valid = json.load(f)
    with open("vatex_public_test_english_v1.1.json") as f:
        test = json.load(f)
    all_vids = [i['videoID'] for i in train + test + valid]
    with open("blacklist.txt") as f:
        blacklist = f.read().split('\n')[:-1]
    black_vids = []
    for vid in all_vids:
        if vid[:11] in blacklist:
            black_vids.append(vid)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for vid in black_vids:
        cursor.execute(f"UPDATE vatex set status='unavailable' where vid = '{vid}'")
    cursor.close()
    conn.commit()
    conn.close()


class DownloadWorker(Thread):
    def __init__(self, dl_queue: Queue, info_lock: Lock,
                 tgt_dir="videos", proxy="http://localhost:7890"):
        Thread.__init__(self)
        self.dl_queue = dl_queue
        self.lock = info_lock
        self.tgt_dir = tgt_dir
        self._base_params = {
            "format": "best[ext=mp4]/best",
            "proxy": proxy,
        }
        self.num_proc = 0

    def run(self):
        while True:
            full_vid = self.obtain_task()
            if full_vid is None:
                print(f"[{current_thread().name}]已无更多任务，结束")
                break
            print(f"[{current_thread().name}]开始下载: {full_vid}")
            try:
                self.download(full_vid)
                status, detail = "successful", None
            except DownloadError as e:
                if "HTTP Error 403" in str(e):
                    status, detail = "failed", str(e)
                elif "Private video" in str(e):
                    status, detail = "unavailable", str(e)
                elif "This video is private" in str(e):
                    status, detail = "unavailable", str(e)
                elif "Video unavailable" in str(e):
                    status, detail = "unavailable", str(e)
                elif "Sign in to confirm your age" in str(e):
                    status, detail = "unavailable", str(e)
                elif "This video has been removed" in str(e):
                    status, detail = "unavailable", str(e)
                else:
                    print(f"[{current_thread().name}]: {e}")
                    status, detail = "failed", str(e)

            if status == 'successful':
                print(f"[{current_thread().name}]下载成功: {full_vid}")
            elif status == 'unavailable':
                print(f"[{current_thread().name}]视频不可用: {full_vid}")
            elif status == 'failed':
                print(f"[{current_thread().name}]下载异常: {full_vid}")
            write_result(full_vid, status, detail)
            self.num_proc += 1

    def obtain_task(self):
        try:
            full_vid = self.dl_queue.get(timeout=10)
            return full_vid
        except Empty:
            return None

    def download(self, full_vid):
        vid = full_vid[:11]
        start, end = full_vid[12:].split('_')
        url = f"https://www.youtube.com/watch?v={vid}"

        def dl_rages_callback(info_dict, ydl):
            return [{'start_time': int(start), 'end_time': int(end)}]

        params = {
            "download_ranges": dl_rages_callback,
            "outtmpl": os.path.join(self.tgt_dir, f"%(id)s_{start}_{end}.%(ext)s"),
        }
        params.update(self._base_params)

        with YoutubeDL(params) as ydl:
            ydl.download([url])


class ProducerWorker(Thread):
    def __init__(self, dl_queue: Queue):
        Thread.__init__(self)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT vid FROM vatex WHERE status='waiting' or status='failed'"
        )
        self.data = cursor.fetchall()
        cursor.close()
        conn.close()

        self.total = len(self.data)
        self.dl_queue = dl_queue

    def run(self):
        print(f"[{current_thread().name}]: 共有{self.total}个任务正在处理")
        for row in self.data:
            self.dl_queue.put(row[0])
        print(f"[{current_thread().name}]: 任务分配完毕")


if __name__ == '__main__':
    lock = Lock()
    dl_queue = Queue(maxsize=1000)
    video_dir = "videos"
    num_workers = 4

    # 生产者
    producer = ProducerWorker(dl_queue)
    producer.daemon = True
    producer.start()
    # 消费者
    worker_list = []
    for _ in range(num_workers):
        w = DownloadWorker(
            dl_queue=dl_queue,
            info_lock=lock,
            tgt_dir=video_dir,
        )
        w.daemon = True
        w.start()
        worker_list.append(w)
    # 监控主进程
    start_time = last_time = time.time()
    while True:
        # 获取存活进程数，假如为0则退出
        num_alive_workers = 0
        num_proc = 0
        for w in worker_list:
            if w.is_alive():
                num_alive_workers += 1
            num_proc += w.num_proc
        if num_alive_workers == 0:
            break  # 结束
        # 距离上一次超过5秒，则输出
        if time.time() - last_time > 5:
            print(f"{int(time.time() - start_time)} | "
                  f"存活进程数：{num_alive_workers}/{num_workers} | "
                  f"任务进度: {num_proc}/{producer.total}")
            last_time = time.time()


