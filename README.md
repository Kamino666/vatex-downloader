# vatex-downloader

A simple vatex dataset downloader. 

一个简单的VATEX数据集（或其他YouTube视频数据集）的下载器，特别为国内网络环境优化（其实就是断点下载和加上代理的参数）。

Features:

+ Interrupt at any time
+ No need to download whole video if you only need a part
+ Blacklist of unavailable videos (in the `.db` file)
+ Multi-threading downloading

支持特性:

+ 可以随时中断下载，下次启动将从断点继续
+ 支持部分下载，假如只需要一个片段就不需要下载整个视频
+ 提供一些已经无法下载的视频黑名单（在`.db`文件里）
+ 多线程下载

## Quick Start

1. Install`sqlite3`：`pip install sqlite3`
2. Install[yt-dlp](https://github.com/yt-dlp/yt-dlp): `pip install yt-dlp`
3. Modify the parameters in `downloader_v2.py` 
   1. Global variable `DATABASE` is the file path of sqlilte database
   2. Global variable `video_dir` is the download directory
   3. Global variable `num_workers` is the number of downloading threads
   4. Global variable `proxy` is the proxy address
4. Run `downloader_v2.py`


1. 安装`sqlite3`：`pip install sqlite3`
2. 安装[yt-dlp](https://github.com/yt-dlp/yt-dlp): `pip install yt-dlp`
3. 更改`downloader_v2.py`代码中的参数（懒得写对外的接口啦） 
   1. 全局变量`DATABASE`是sqlilte的数据库文件地址
   2. 全局变量`video_dir`是下载目录
   3. 全局变量`num_workers`是下载线程数
   4. 全局变量`proxy`是代理地址
4. 运行`downloader_v2.py`

   
    