from yt_dlp import YoutubeDL, DownloadError
from threading import Thread, Lock, current_thread
from queue import Queue, Empty
import pandas as pd
import os
import time

"""
vid             status                                             details
<11>_<6>_<6>    waiting/downloading/successful/unavailable/failed  详细信息

访问太频繁会报错
ERROR: unable to download video data: HTTP Error 403: Forbidden
网络报错
ERROR: unable to download video data: <urlopen error [WinError 10054] 远程主机强迫关闭了一个现有的连接。>
"""


class DownloadWorker(Thread):
    def __init__(self, dl_queue: Queue, dl_info: str, info_lock: Lock,
                 tgt_dir="videos", proxy="http://localhost:7890"):
        Thread.__init__(self)
        self.dl_queue = dl_queue
        self.dl_info = dl_info
        self.lock = info_lock
        self.tgt_dir = tgt_dir
        self._base_params = {
            "format": "best[ext=mp4]/best",
            "proxy": proxy,
        }
        self.num_proc = 0

    def run(self):
        while True:
            full_vid = self.obtain_task_v2()
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
            self.write_result(full_vid, status, detail)
            self.num_proc += 1

    def obtain_task(self):
        try:
            # 1. 拿锁
            self.lock.acquire()
            # 2. 获取任务
            full_vid = self.dl_queue.get()
            # 3. 占据任务
            df = pd.read_csv(self.dl_info)
            df.loc[df['vid'] == full_vid, 'status'] = "downloading"
            df.to_csv(self.dl_info, index=False)
        finally:
            # 4. 放锁
            self.lock.release()
        return full_vid

    def obtain_task_v2(self):
        try:
            full_vid = self.dl_queue.get(timeout=10)
            return full_vid
        except Empty:
            return None

    def write_result(self, full_vid, status, details=None):
        try:
            # 1. 拿锁
            self.lock.acquire()
            # 2. 写结果
            df = pd.read_csv(self.dl_info)
            df.loc[df['vid'] == full_vid, ('status', 'details')] = status, details
            df.to_csv(self.dl_info, index=False)
        finally:
            # 3. 放锁
            self.lock.release()

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
    def __init__(self, dl_queue: Queue, dl_info: str):
        Thread.__init__(self)
        df = pd.read_csv(dl_info)
        self.data = pd.concat([
            df[df['status'] == "waiting"],
            df[df['status'] == "failed"],
        ])
        self.total = self.data.shape[0]
        self.dl_queue = dl_queue

    def run(self):
        print(f"[{current_thread().name}]: 共有{self.total}个任务正在处理")
        for row in self.data.itertuples():
            self.dl_queue.put(getattr(row, "vid"))
        print(f"[{current_thread().name}]: 任务分配完毕")


if __name__ == '__main__':
    lock = Lock()
    dl_queue = Queue(maxsize=1000)
    video_dir = "videos"
    download_info = "download_info.csv"
    num_workers = 4

    # 生产者
    producer = ProducerWorker(dl_queue, download_info)
    producer.daemon = True
    producer.start()
    # 消费者
    worker_list = []
    for _ in range(num_workers):
        w = DownloadWorker(
            dl_queue=dl_queue,
            dl_info=download_info,
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
        # 距离上一次超过20秒，则输出
        if time.time() - last_time > 20:
            print(f"{int(time.time() - start_time)} | "
                  f"存活进程数：{num_alive_workers}/{num_workers} | "
                  f"任务进度: {num_proc}/{producer.total}")
            last_time = time.time()



