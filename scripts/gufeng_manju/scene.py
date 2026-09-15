# -*- coding: utf-8 -*-
"""
古风书房场景 + 国漫条漫2D扁平漫画人物（分层绘制，保证五官全程一致）
- 所有五官为静态图层，仅在帧间做亚像素平移/局部重绘 → 无扭曲、无闪烁
- 人物侧脸对镜头（3/4侧），长发青年男子，立于书桌前
"""
import math
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
SS = 2  # 超采样倍率，勾线更干净

# ---------------- 调色板（国漫·柔和干净） ----------------
C = {
    "wall_top":   (250, 242, 226),
    "wall_bot":   (238, 224, 200),
    "beam":       (186, 146, 102),
    "beam_dk":    (150, 112, 74),
    "floor":      (206, 170, 122),
    "floor_dk":   (178, 140, 98),
    "desk":       (188, 142, 92),
    "desk_top":   (218, 174, 122),
    "desk_dk":    (146, 102, 62),
    "paper":      (246, 243, 233),
    "window_gl":  (255, 250, 234),
    "window_fr":  (156, 116, 76),
    "lattice":    (182, 142, 98),
    "plant":      (128, 168, 112),
    "plant_dk":   (96, 136, 88),
    "pot":        (166, 116, 88),
    "skin":       (247, 223, 200),
    "skin_sh":    (231, 199, 172),
    "skin_line":  (150, 104, 78),
    "hair":       (44, 38, 46),
    "hair_hl":    (76, 66, 82),
    "hair_line":  (26, 22, 30),
    "robe":       (242, 240, 236),
    "robe_sh":    (216, 216, 216),
    "robe_line":  (96, 96, 108),
    "inner":      (94, 132, 148),
    "inner_dk":   (72, 106, 124),
    "sash":       (152, 74, 70),
    "sash_dk":    (118, 54, 52),
    "eye_white":  (252, 250, 248),
    "iris":       (74, 62, 78),
    "iris_dk":    (40, 32, 44),
    "pupil":      (24, 20, 28),
    "mouth_in":   (146, 86, 84),
    "mouth_dk":   (110, 58, 60),
    "teeth":      (250, 248, 244),
}

def S(v):
    """超采样坐标"""
    return v * SS


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def new_layer():
    return Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))


# ============================================================
# 背景层：室内古风书房
# ============================================================
def draw_background():
    d = ImageDraw.Draw(new_layer())
    L = new_layer()

    # --- 墙面（暖木色渐变）---
    # 注意：必须以 S(H)（超采样高度）绘制，否则超采样域下半部分会残留透明→合成后发黑
    grad = Image.new("RGB", (1, H * SS), C["wall_top"])
    gp = grad.load()
    for y in range(H * SS):
        t = y / (H * SS)
        gp[0, y] = tuple(int(C["wall_top"][i] + (C["wall_bot"][i] - C["wall_top"][i]) * t) for i in range(3))
    grad = grad.resize((W * SS, H * SS), Image.NEAREST).convert("RGB")
    L.paste(grad, (0, 0))

    d = ImageDraw.Draw(L)

    # --- 地板（透视） ---
    floor_y = 748
    d.polygon([(0, S(floor_y)), (S(W), S(floor_y)), (S(W), S(H)), (0, S(H))], fill=rgba(C["floor"]))
    # 地板板缝
    # 地板：横向板条（近疏远密）+ 纵向板缝（透视汇聚）
    for i in range(1, 9):
        t = (i / 8.0) ** 1.9
        y = floor_y + (H - floor_y) * t
        d.line([(0, S(y)), (S(W), S(y))], fill=rgba(C["floor_dk"], 80), width=S(3))
    for i in range(0, 15):
        xb = -220 + i * 175
        d.line([(S(xb), S(floor_y)), (S(xb - 150), S(H))], fill=rgba(C["floor_dk"], 70), width=S(3))
    # 踢脚线（浅色，替代深色围边，避免视觉像"水面"）
    d.rectangle([S(0), S(floor_y - 24), S(W), S(floor_y)], fill=rgba((214, 194, 166)))
    d.line([(S(0), S(floor_y - 24)), (S(W), S(floor_y - 24))], fill=rgba(C["desk_dk"], 130), width=S(3))
    d.line([(S(0), S(floor_y)), (S(W), S(floor_y))], fill=rgba(C["desk_dk"], 150), width=S(4))

    # --- 左侧窗（柔和环境光来源） ---
    wx0, wy0, wx1, wy1 = 92, 196, 556, 700
    d.rectangle([S(wx0) - S(14), S(wy0) - S(14), S(wx1) + S(14), S(wy1) + S(14)], fill=rgba(C["window_fr"]))
    d.rectangle([S(wx0), S(wy0), S(wx1), S(wy1)], fill=rgba(C["window_gl"]))
    # 窗棂
    for i in range(1, 4):
        x = wx0 + (wx1 - wx0) * i / 4
        d.line([(S(x), S(wy0)), (S(x), S(wy1))], fill=rgba(C["lattice"]), width=S(8))
    for j in range(1, 4):
        y = wy0 + (wy1 - wy0) * j / 4
        d.line([(S(wx0), S(y)), (S(wx1), S(y))], fill=rgba(C["lattice"]), width=S(8))
    d.rectangle([S(wx0), S(wy0), S(wx1), S(wy1)], outline=rgba(C["window_fr"]), width=S(9))
    # 窗外远景枝影
    d.line([(S(wx0+40), S(wy1-120)), (S(wx1-30), S(wy0+70))], fill=rgba((206, 196, 160), 160), width=S(4))

    # --- 右侧书架 ---
    bx0, by0, bx1, by1 = 1392, 150, 1880, 812
    d.rectangle([S(bx0), S(by0), S(bx1), S(by1)], fill=rgba((172, 132, 92)))
    d.rectangle([S(bx0+18), S(by0+18), S(bx1-18), S(by1-18)], fill=rgba(C["beam"]))
    shelf_ys = [by0 + 18 + (by1 - by0 - 36) * k / 4 for k in range(1, 4)]
    book_cols = [(168, 92, 84), (110, 130, 112), (92, 110, 148), (176, 148, 96), (132, 96, 138)]
    for si, sy in enumerate(shelf_ys):
        d.rectangle([S(bx0+18), S(sy)-S(9), S(bx1-18), S(sy)+S(9)], fill=rgba((154, 116, 80)))
        # 书
        x = bx0 + 46
        k = 0
        while x < bx1 - 60:
            bw = 22 + ((si * 7 + k * 5) % 18)
            bh = 92 + ((si * 13 + k * 11) % 34)
            col = book_cols[(si + k) % len(book_cols)]
            d.rectangle([S(x), S(sy - 9 - bh), S(x + bw), S(sy - 9)], fill=rgba(col))
            d.rectangle([S(x), S(sy - 9 - bh), S(x + bw), S(sy - 9)], outline=rgba((70, 58, 46), 180), width=S(2))
            x += bw + 6
            k += 1
    d.rectangle([S(bx0), S(by0), S(bx1), S(by1)], outline=rgba((132, 96, 60)), width=S(8))
    # 架前矮柜（书架与地板之间的过渡，避免死黑）
    d.rectangle([S(bx0 - 10), S(by1 - 96), S(bx1 + 10), S(by1 + 26)], fill=rgba((196, 152, 108)))
    d.rectangle([S(bx0 - 10), S(by1 - 96), S(bx1 + 10), S(by1 - 74)], fill=rgba((214, 172, 124)))
    d.line([(S(bx0 - 10), S(by1 - 96)), (S(bx1 + 10), S(by1 - 96))], fill=rgba((140, 100, 62)), width=S(4))
    d.line([(S(bx0 - 10), S(by1 - 74)), (S(bx1 + 10), S(by1 - 74))], fill=rgba((140, 100, 62)), width=S(3))

    # --- 横梁 ---
    d.rectangle([0, 0, S(W), S(96)], fill=rgba(C["beam"]))
    d.rectangle([0, S(96), S(W), S(112)], fill=rgba(C["beam_dk"]))

    # --- 挂轴背板（覆盖书架左侧的墙面，消除死黑） ---
    d.rectangle([S(884), S(140), S(1380), S(752)], fill=rgba((247, 237, 218)))
    d.rectangle([S(884), S(140), S(1380), S(752)], outline=rgba((216, 194, 164)), width=S(3))
    # 背板下方到地板之间的墙面（不留缝）
    d.rectangle([S(884), S(752), S(1380), S(792)], fill=rgba((240, 226, 202)))

    # --- 挂轴（中偏右） ---
    sx0, sy0, sx1, sy1 = 1010, 208, 1210, 620
    d.rectangle([S(sx0), S(sy0), S(sx1), S(sy1)], fill=rgba((236, 226, 206)))
    d.rectangle([S(sx0), S(sy0), S(sx1), S(sy1)], outline=rgba(C["beam_dk"]), width=S(6))
    d.rectangle([S(sx0-16), S(sy0-26), S(sx1+16), S(sy0-6)], fill=rgba(C["beam_dk"]))
    d.rectangle([S(sx0-16), S(sy1+6), S(sx1+16), S(sy1+26)], fill=rgba(C["beam_dk"]))
    # 水墨意象（抽象山水）
    d.polygon([(S(sx0+30), S(sy1-70)), (S(sx0+120), S(sy0+120)), (S(sx1-30), S(sy1-70))],
              fill=rgba((176, 180, 178), 150))
    d.polygon([(S(sx0+60), S(sy1-70)), (S(sx0+130), S(sy0+210)), (S(sx1-60), S(sy1-70))],
              fill=rgba((146, 150, 150), 130))

    # --- 窗光光束（柔和） ---
    return L


def add_light_beams(img):
    """柔和窗光光束（叠加在背景之上，低透明度暖白）"""
    beam = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    wx0, wy0, wx1, wy1 = 92, 196, 556, 700
    # 主光束（从窗斜射至桌面，边界柔和、覆盖全高，不形成硬三角）
    bd.polygon([(S(wx0 - 30), S(wy0)), (S(wx1 + 30), S(wy0)),
                (S(wx1 + 700), S(H * SS)), (S(wx0 - 220), S(H * SS))],
               fill=(255, 252, 240, 22))
    # 窗口溢光（围绕窗框的柔和 glow）
    bd.rectangle([S(wx0 - 110), S(wy0 - 110), S(wx1 + 110), S(wy1 + 110)],
                 fill=(255, 250, 228, 26))
    beam = beam.filter(ImageFilter.GaussianBlur(S(86)))
    return Image.alpha_composite(img, beam)


# ============================================================
# 书桌层（人物之后绘制，形成"站在桌前"遮挡关系）
# ============================================================
def draw_desk():
    L = new_layer()
    d = ImageDraw.Draw(L)
    dx0, dy0, dx1, dy1 = 300, 742, 1330, 812
    # 桌面
    d.rectangle([S(dx0), S(dy0), S(dx1), S(dy1)], fill=rgba(C["desk_top"]))
    d.rectangle([S(dx0), S(dy1), S(dx1), S(dy1 + 26)], fill=rgba(C["desk"]))
    d.line([(S(dx0), S(dy0)), (S(dx1), S(dy0))], fill=rgba(C["desk_dk"]), width=S(5))
    d.line([(S(dx0), S(dy1 + 26)), (S(dx1), S(dy1 + 26))], fill=rgba(C["desk_dk"]), width=S(5))
    # 桌腿 / 侧板
    for lx in (dx0 + 40, dx1 - 90):
        d.rectangle([S(lx), S(dy1 + 26), S(lx + 50), S(dy1 + 190)], fill=rgba(C["desk_dk"]))
    d.rectangle([S(dx0), S(dy1 + 26), S(dx0 + 26), S(dy1 + 210)], fill=rgba(C["desk"]))
    d.rectangle([S(dx1 - 26), S(dy1 + 26), S(dx1), S(dy1 + 210)], fill=rgba(C["desk"]))

    # 桌上：书册
    d.polygon([(S(560), S(dy0-4)), (S(760), S(dy0-14)), (S(770), S(dy0+16)), (S(568), S(dy0+22))],
              fill=rgba(C["paper"]))
    d.polygon([(S(560), S(dy0-4)), (S(760), S(dy0-14)), (S(770), S(dy0+16)), (S(568), S(dy0+22))],
              outline=rgba(C["desk_dk"]), width=S(3))
    d.polygon([(S(742), S(dy0-26)), (S(902), S(dy0-30)), (S(910), S(dy0+2)), (S(750), S(dy0+6))],
              fill=rgba((238, 233, 220)))
    d.polygon([(S(742), S(dy0-26)), (S(902), S(dy0-30)), (S(910), S(dy0+2)), (S(750), S(dy0+6))],
              outline=rgba(C["desk_dk"]), width=S(3))

    # 桌面柔和投影（统一加在桌面元素下）
    sh = new_layer()
    sd = ImageDraw.Draw(sh)
    for (ex0, ey0, ex1, ey1) in ((556, dy0+18, 774, dy0+40), (738, dy0+2, 914, dy0+26),
                                 (1022, dy0-40, 1188, dy0-16), (1192, dy0-26, 1308, dy0+14)):
        sd.ellipse([S(ex0), S(ey0), S(ex1), S(ey1)], fill=(120, 84, 52, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(S(7)))
    L = Image.alpha_composite(L, sh)
    d = ImageDraw.Draw(L)

    # 笔架 + 毛笔
    d.rectangle([S(1030), S(dy0-58), S(1180), S(dy0-46)], fill=rgba(C["beam_dk"]))
    for i, px in enumerate((1050, 1096, 1142)):
        d.line([(S(px), S(dy0-52)), (S(px - 16), S(dy0-6))], fill=rgba((92, 66, 44)), width=S(9))
        d.line([(S(px - 16), S(dy0-6)), (S(px - 22), S(dy0 + 2))], fill=rgba((40, 34, 34)), width=S(8))
    # 砚台
    d.ellipse([S(1200), S(dy0-30), S(1300), S(dy0+4)], fill=rgba((70, 66, 70)))
    d.ellipse([S(1214), S(dy0-22), S(1286), S(dy0-4)], fill=rgba((46, 44, 50)))
    return L
