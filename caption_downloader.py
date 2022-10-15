# -*- coding: utf-8 -*-

# Sample Python code for youtube.captions.download
# NOTE: This sample code downloads a file and can't be executed via this
#       interface. To test this sample, you must run it locally using your
#       own API credentials.

# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os
import io
import json

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from threading import Thread, Lock, current_thread
from queue import Queue, Empty
import sqlite3
from downloader_v2 import DATABASE

from googleapiclient.http import MediaIoBaseDownload

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
client_secrets_file = "client_secret_958543966650-u4m3ls9ssuk41a5l99g6j7hrt3kt2d64.apps.googleusercontent.com.json"
api_service_name = "youtube"
api_version = "v3"


class DownloadWorker(Thread):
    def __init__(self, dl_queue: Queue, tgt_dir="asr", ):
        Thread.__init__(self)
        self.dl_queue = dl_queue
        self.tgt_dir = tgt_dir
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
            except Exception as e:
                print(e)
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
        # start, end = full_vid[12:].split('_')
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials,
        )

        # 获取ASR列表
        request = youtube.captions().list(
            part="snippet",
            videoId=vid
        )
        response: dict = request.execute()
        asr_id = response['items'][0]['id']

        # 下载ASR数据
        request = youtube.captions().download(id=asr_id)
        fh = io.FileIO(f"{full_vid}.txt", "wb")
        download = MediaIoBaseDownload(fh, request)
        complete = False
        while not complete:
            status, complete = download.next_chunk()


class ProducerWorker(Thread):
    def __init__(self, dl_queue: Queue):
        Thread.__init__(self)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT vid FROM vatex WHERE status='successful' and asr=null"
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


# def main():
#     # Disable OAuthlib's HTTPS verification when running locally.
#     # *DO NOT* leave this option enabled in production.
#     # os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
#     #
#     # api_service_name = "youtube"
#     # api_version = "v3"
#     # client_secrets_file = "client_secret_958543966650-u4m3ls9ssuk41a5l99g6j7hrt3kt2d64.apps.googleusercontent.com.json"
#
#     # Get credentials and create an API client
#     flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
#         client_secrets_file, scopes)
#     credentials = flow.run_console()
#     youtube = googleapiclient.discovery.build(
#         api_service_name, api_version, credentials=credentials,
#     )
#
#     request = youtube.captions().download(
#         id="cMSse6J-wfU"
#     )
#     # TODO: For this request to work, you must replace "YOUR_FILE"
#     #       with the location where the downloaded content should be written.
#     fh = io.FileIO("test_ytb_caption.txt", "wb")
#
#     download = MediaIoBaseDownload(fh, request)
#     complete = False
#     while not complete:
#       status, complete = download.next_chunk()


if __name__ == "__main__":
    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    # main()
