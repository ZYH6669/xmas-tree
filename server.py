# -*- coding: utf-8 -*-
"""
一键把圣诞树变成“局域网链接”
================================
双击运行（或 python server.py），它会：
  1. 在本机 8000 端口起一个网页服务
  2. 打印出几个可以给手机 / 朋友电脑打开的网址
  3. 自动用默认浏览器打开

手机连**同一个 WiFi**，把控制台里的 http://192.168.x.x:8000 输进浏览器就能看。
（第一次运行 Windows 可能弹防火墙提示，点“允许访问”。）

命令行参数：python server.py 8080    # 换端口
"""

import functools
import http.server
import os
import socket
import sys
import threading
import webbrowser

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

try:                          # 老式 Windows 控制台是 GBK，避免特殊字符报错
    sys.stdout.reconfigure(errors="replace", line_buffering=True)
except Exception:
    pass


def lan_ips():
    """尽量拿到本机在 WiFi 里的 IP。"""
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))          # 不会真的发包，只是让系统选网卡
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    if not ips:
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = info[4][0]
                if not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
        except Exception:
            pass
    return ips


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)

    httpd = None
    port = PORT
    for _ in range(20):                     # 端口被占用就往后顺延
        try:
            httpd = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler)
            break
        except OSError:
            port += 1
    if httpd is None:
        print("端口都被占用了，换个端口试试：python server.py 9000")
        return

    ips = lan_ips()
    print()
    print("  圣诞树已经亮起来了")
    print("  " + "-" * 46)
    print(f"  本机：   http://127.0.0.1:{port}/")
    for ip in ips:
        print(f"  手机/朋友：http://{ip}:{port}/")
    print("  " + "-" * 46)
    print("  手机连同一个 WiFi，把上面的地址输进浏览器即可。")
    print("  想给某个人：地址后面加  ?to=小明")
    print("  关掉这个窗口（或按 Ctrl+C）就停止分享。")
    print()

    threading.Timer(0.6, lambda: webbrowser.open(f"http://127.0.0.1:{port}/")).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
