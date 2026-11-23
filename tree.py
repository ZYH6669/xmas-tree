# -*- coding: utf-8 -*-
"""
代码圣诞树（Python + tkinter 版）
=================================
只用 Python 自带库，不需要 pip 安装任何东西。

运行：
    python tree.py
    python tree.py 小明        # 第二行显示 TO:小明

快捷键：
    Esc  退出        F  全屏 / 还原       空格  暂停/继续
"""

import math
import os
import random
import sys

import tkinter as tk

# ---------------------------------------------------------------- 可以改这里
GREET = "Merry Christmas"      # 第一行
TO = sys.argv[1] if len(sys.argv) > 1 else "YOU"

WIDTH, HEIGHT = 1100, 740       # 初始窗口大小（会按屏幕自动收一点）
FRAME_MS = 33                   # 约 30 帧/秒

TAU = math.pi * 2
rnd = random.uniform

# 颜色权重（亮 → 暗）
PALETTE = [
    (0.36, "#ffffff"),
    (0.42, "#d6f2ff"),
    (0.12, "#9fe0ff"),
    (0.10, "#6fb8ff"),
]

# 树的三维参数，和网页版保持一致
TREE_H, TREE_R, TREE_BOT = 600.0, 285.0, 300.0
FOCAL, CAM_Z, TILT = 1390.0, 1250.0, 0.10


def pick_color():
    weights = [w for w, _ in PALETTE]
    colors = [c for _, c in PALETTE]
    return random.choices(colors, weights=weights, k=1)[0]


class Particle:
    __slots__ = ("x", "y", "z", "r", "color", "tw", "ph", "item")

    def __init__(self, x, y, z, r, color, tw=0.2, ph=0.0):
        self.x, self.y, self.z = x, y, z
        self.r = r
        self.color = color
        self.tw = tw          # 闪烁幅度
        self.ph = ph          # 闪烁相位
        self.item = None


def build_tree():
    """螺旋灯带 + 内部雾 + 底部星尘旋涡 + 树梢爱心。"""
    pts = []

    # 1) 螺旋灯带
    strands, per = 6, 150
    for s in range(strands):
        for i in range(per):
            u = (i / per) ** 1.3
            ang = u * TAU * 5.2 + s / strands * TAU + rnd(-0.12, 0.12)
            rad = TREE_R * (1 - u) ** 1.04 + rnd(-6, 6)
            pts.append(Particle(
                math.cos(ang) * rad,
                TREE_BOT - u * TREE_H + rnd(-3, 3),
                math.sin(ang) * rad,
                rnd(1.2, 2.4), pick_color(), rnd(0.15, 0.8), rnd(0, TAU),
            ))

    # 2) 内部雾状填充
    for _ in range(170):
        u = 1 - math.sqrt(random.random())
        rad = TREE_R * (1 - u) ** 1.04 * math.sqrt(random.random()) * 0.92
        ang = rnd(0, TAU)
        pts.append(Particle(
            math.cos(ang) * rad,
            TREE_BOT - u * TREE_H + rnd(-6, 6),
            math.sin(ang) * rad,
            rnd(0.9, 1.7), pick_color(), rnd(0, 0.3), rnd(0, TAU),
        ))

    # 3) 底部星尘旋涡
    rim = TREE_R * 1.12
    for i in range(210):
        u = (i / 210) ** 0.7
        r = rim * u
        ang = u * TAU * 2.4 + rnd(-0.1, 0.1)
        pts.append(Particle(
            math.cos(ang) * r,
            TREE_BOT + 6 + 26 * u ** 1.7 + rnd(-8, 8),
            math.sin(ang) * r,
            rnd(1.1, 2.1), pick_color(), rnd(0.1, 0.6), rnd(0, TAU),
        ))

    # 4) 树梢爱心
    k, hy = 1.42, TREE_BOT - TREE_H - 52
    for _ in range(90):
        t = rnd(0, TAU)
        hx = 16 * math.sin(t) ** 3
        yy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        g = rnd(0.85, 1.0) if random.random() < 0.3 else math.sqrt(random.random())
        pts.append(Particle(
            hx * g * k, hy - yy * g * k, 0,
            rnd(1.1, 2.0),
            random.choice(["#ffb0e0", "#ff8fd0", "#c9a6ff", "#ffffff"]),
            rnd(0.2, 0.7), rnd(0, TAU),
        ))
    return pts


def project(p, rot, cos_t, sin_t, cx, cy, scale):
    """绕 Y 轴旋转 → 轻微俯仰 → 透视投影。"""
    x1 = p.x * rot[0] - p.z * rot[1]
    z1 = p.x * rot[1] + p.z * rot[0]
    y1 = p.y * cos_t - z1 * sin_t
    z2 = p.y * sin_t + z1 * cos_t
    d = CAM_Z + z2
    if d < 60:
        return None
    k = FOCAL / d * scale
    near = max(0.0, min(1.0, (z2 + 340) / 680))
    return cx + x1 * k, cy + y1 * k, near


class TreeApp:
    def __init__(self, root):
        self.root = root
        self.paused = False
        self.rot = 0.62

        root.title("Merry Christmas")
        root.configure(bg="black")

        self.canvas = tk.Canvas(root, bg="#04060b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(WIDTH, sw - 60), min(HEIGHT, sh - 120)
        root.geometry(f"{max(640, w)}x{max(480, h)}+{(sw - w) // 2}+{(sh - h) // 3}")

        self.build_scene()

        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<space>", self.toggle_pause)
        root.bind("<Key-f>", self.toggle_fullscreen)
        root.bind("<Key-F>", self.toggle_fullscreen)

    # ------------------------------------------------------------ 场景搭建
    def build_scene(self):
        c = self.canvas
        self.particles = build_tree()

        # 背景星
        for _ in range(120):
            x, y = rnd(0, 1200), rnd(0, 800)
            r = rnd(0.5, 1.6)
            shade = random.choice(["#2a3d52", "#3b5876", "#6f8fae", "#cfe6ff"])
            c.create_oval(x, y, x + r, y + r, fill=shade, outline="")

        # 树的粒子
        for p in self.particles:
            p.item = c.create_oval(0, 0, 1, 1, fill=p.color, outline="")

        # 雪：记录半径，避免传送时把椭圆拉长
        self.snow = []
        for _ in range(46):
            x, y = rnd(0, 1200), rnd(0, 800)
            r = rnd(1.0, 2.4)
            it = c.create_oval(x, y, x + r * 2, y + r * 2, fill="#eaf4ff", outline="")
            self.snow.append([it, r * 2, rnd(0.8, 2.4), rnd(-0.5, 0.5)])

        # 文案
        fs = max(18, int(self.canvas_height() * 0.05))
        x, y = int(self.canvas_width() * 0.055), int(self.canvas_height() * 0.335)
        self.text1 = c.create_text(x, y, anchor="nw", text=GREET,
                                   fill="#f3faff", font=("Georgia", fs, "italic"))
        self.text2 = c.create_text(x, y + int(fs * 1.5), anchor="nw", text="TO:" + TO,
                                   fill="#dfeeff",
                                   font=("Georgia", int(fs * 0.72), "italic"))

    def canvas_width(self):
        return self.canvas.winfo_width() or WIDTH

    def canvas_height(self):
        return self.canvas.winfo_height() or HEIGHT

    # ------------------------------------------------------------ 交互
    def toggle_pause(self, _e=None):
        self.paused = not self.paused

    def toggle_fullscreen(self, _e=None):
        self.root.attributes("-fullscreen",
                             not self.root.attributes("-fullscreen"))

    # ------------------------------------------------------------ 每帧
    def tick(self):
        if not self.paused:
            self.rot += 0.012
        self.draw()
        self.root.after(FRAME_MS, self.tick)

    def draw(self):
        c = self.canvas
        W, H = self.canvas_width(), self.canvas_height()
        scale = min(W / 1400.0, H / 1150.0)
        cx, cy = W * 0.5, H * 0.5 - 30 * scale
        cos_t, sin_t = math.cos(TILT), math.sin(TILT)
        rot = (math.cos(self.rot), math.sin(self.rot))

        for p in self.particles:
            res = project(p, rot, cos_t, sin_t, cx, cy, scale)
            if res is None:
                continue
            x, y, near = res
            r = p.r * 0.6 * (0.6 + 0.8 * near)
            c.coords(p.item, x - r, y - r, x + r, y + r)

        # 雪（宽高保持不变，掉出屏幕后从顶部重生）
        for s in self.snow:
            it, w, vy, vx = s
            x1, y1, x2, y2 = c.coords(it)
            x1 += vx + math.sin(self.rot * 3 + y1 * 0.02) * 0.4
            y1 += vy
            if y1 > H:
                x1, y1 = rnd(0, W), -6
            c.coords(it, x1, y1, x1 + w, y1 + w)

        # 文案跟着窗口走
        fs = max(18, int(H * 0.05))
        tx, ty = int(W * 0.055), int(H * 0.335)
        c.coords(self.text1, tx, ty)
        c.coords(self.text2, tx, ty + int(fs * 1.5))


def main():
    if os.name == "nt":                     # 让 Tk 按物理像素工作，避免高分屏错位
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    root = tk.Tk()
    app = TreeApp(root)

    if os.environ.get("TREE_TEST"):         # 自检：跑 40 帧就退出
        root.withdraw()
        for _ in range(40):
            app.draw()
        root.update()
        root.destroy()
        print("ok")
        return

    app.tick()
    root.mainloop()


if __name__ == "__main__":
    main()
