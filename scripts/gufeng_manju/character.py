# -*- coding: utf-8 -*-
"""
国漫条漫 2D 扁平漫画人物 —— 分层绘制
设计要点（对应客户硬要求）：
  1. 「五官全程保持一致」→ 五官全部画在固定的局部坐标系，逐帧只做整体亚像素位移，
     绝不做形变/重绘 → 数学上保证零漂移、零扭曲
  2. 「口型」→ 只重绘嘴部局部小图（下颚线保持静止，避免面部扭曲）
  3. 「眼神微动」→ 只重绘虹膜/瞳孔局部（眼型轮廓静止）
  4. 「呼吸微动」→ 上半身整体正弦微位移 + 肩线局部呼吸缩放
"""
import math
from PIL import Image, ImageDraw, ImageFilter
from scene import W, H, SS, C, S, rgba, new_layer

# ---- 人物基座（超采样域坐标） ----
ANCHOR = dict(cx=640, eye_y=452, chin_y=540)


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ============================================================
# 头发（后层）
# ============================================================
def draw_hair_back():
    L = new_layer()
    d = ImageDraw.Draw(L)
    cx = ANCHOR["cx"]
    # 长发垂落（背侧）
    d.polygon([
        (S(cx - 118), S(336)), (S(cx - 152), S(440)), (S(cx - 178), S(600)),
        (S(cx - 182), S(760)), (S(cx - 130), S(766)), (S(cx - 120), S(616)),
        (S(cx - 106), S(474)), (S(cx - 92), S(360)),
    ], fill=rgba(C["hair"]), outline=rgba(C["hair_line"]), width=S(3))
    d.polygon([
        (S(cx + 86), S(330)), (S(cx + 146), S(420)), (S(cx + 186), S(560)),
        (S(cx + 196), S(752)), (S(cx + 150), S(758)), (S(cx + 140), S(596)),
        (S(cx + 112), S(452)), (S(cx + 96), S(360)),
    ], fill=rgba(C["hair"]), outline=rgba(C["hair_line"]), width=S(3))
    # 发丝高光（长弧线，条漫质感）
    for off, wd, al in ((-140, 5, 80), (-162, 3, 60), (166, 4, 75), (144, 3, 55)):
        d.line([(S(cx + off), S(400)), (S(cx + off + (14 if off > 0 else -12)), S(620))],
               fill=rgba(C["hair_hl"], al), width=S(wd))
    return L


# ============================================================
# 颈 / 肩 / 衣袍（含呼吸驱动）
# ============================================================
def draw_body(breath=0.0, sway=0.0):
    """breath: 0~1 呼吸相位；sway: 水平微摆（像素，亚采样前）"""
    L = new_layer()
    d = ImageDraw.Draw(L)
    cx = ANCHOR["cx"] + sway
    by = breath * 4.0                    # 呼吸纵向微位移（超采样前像素）
    sh = 1.0 + breath * 0.006            # 肩线呼吸微扩
    _ = sh  # 肩宽呼吸量极小，靠 by 表现即可

    # --- 脖子 ---
    d.polygon([(S(cx - 46), S(506 + by)), (S(cx + 58), S(504 + by)),
               (S(cx + 72), S(602 + by)), (S(cx - 60), S(606 + by))], fill=rgba(C["skin"]))
    # 下颌投影
    d.polygon([(S(cx - 46), S(506 + by)), (S(cx + 58), S(504 + by)),
               (S(cx + 60), S(536 + by)), (S(cx - 48), S(538 + by))], fill=rgba(C["skin_sh"]))

    # --- 内衬（交领） ---
    d.polygon([(S(cx - 64), S(590 + by)), (S(cx + 24), S(610 + by)), (S(cx + 32), S(744 + by)),
               (S(cx - 120), S(754 + by))], fill=rgba(C["inner"]))
    d.polygon([(S(cx + 32), S(610 + by)), (S(cx + 78), S(600 + by)), (S(cx + 152), S(754 + by)),
               (S(cx + 36), S(744 + by))], fill=rgba(C["inner_dk"]))

    # --- 外袍本体 ---
    robe = [
        (S(cx - 130), S(602 + by)), (S(cx - 70), S(578 + by)), (S(cx + 84), S(586 + by)),
        (S(cx + 152), S(602 + by)), (S(cx + 236), S(786 + by)), (S(cx + 252), S(900 + by)),
        (S(cx - 248), S(900 + by)), (S(cx - 236), S(782 + by)),
    ]
    d.polygon(robe, fill=rgba(C["robe"]))
    # 衣纹（扁平漫画勾线）
    for (px0, py0, px1, py1, w, col) in (
        (-210, 700, -152, 848, 4, C["robe_line"]),
        (-152, 656, -110, 826, 3, C["robe_sh"]),
        (174, 682, 216, 842, 4, C["robe_line"]),
        (138, 648, 124, 822, 3, C["robe_sh"]),
    ):
        d.line([(S(cx + px0), S(py0 + by)), (S(cx + px1), S(py1 + by))],
               fill=rgba(col, 150), width=S(w))
    # 外袍轮廓
    d.line([(S(cx - 130), S(602 + by)), (S(cx - 236), S(786 + by)), (S(cx - 248), S(900 + by))],
           fill=rgba(C["robe_line"]), width=S(4))
    d.line([(S(cx + 150), S(610 + by)), (S(cx + 236), S(786 + by)), (S(cx + 252), S(900 + by))],
           fill=rgba(C["robe_line"]), width=S(4))
    # 交领轮廓
    d.line([(S(cx - 130), S(602 + by)), (S(cx - 64), S(588 + by)), (S(cx + 80), S(596 + by)),
            (S(cx + 150), S(610 + by))], fill=rgba(C["robe_line"]), width=S(4))
    d.line([(S(cx - 64), S(588 + by)), (S(cx + 26), S(612 + by)), (S(cx + 34), S(742 + by))],
           fill=rgba(C["desk_dk"]), width=S(4))

    # --- 腰带 ---
    d.polygon([(S(cx - 208), S(778 + by)), (S(cx + 218), S(782 + by)),
               (S(cx + 226), S(834 + by)), (S(cx - 216), S(830 + by))], fill=rgba(C["sash"]))
    d.polygon([(S(cx - 216), S(830 + by)), (S(cx + 226), S(834 + by)),
               (S(cx + 224), S(850 + by)), (S(cx - 214), S(846 + by))], fill=rgba(C["sash_dk"]))
    return L


# ============================================================
# 头部（静态五官，保证全程一致）
# ============================================================
def draw_head():
    """返回 (整头图层, 嘴部区域框, 眼部区域框)
    头部完全静态：所有帧复用同一张位图，仅做整体亚像素位移"""
    L = new_layer()
    d = ImageDraw.Draw(L)
    cx = ANCHOR["cx"]
    ex, ey = cx, ANCHOR["eye_y"]

    # --- 脸型（3/4 侧脸，尖下巴） ---
    face = [
        (S(cx - 98), S(348)), (S(cx - 110), S(408)), (S(cx - 102), S(466)),
        (S(cx - 78), S(510)), (S(cx - 36), S(540)), (S(cx + 22), S(548)),
        (S(cx + 76), S(530)), (S(cx + 106), S(488)), (S(cx + 116), S(432)),
        (S(cx + 110), S(378)), (S(cx + 76), S(336)),
    ]
    d.polygon(face, fill=rgba(C["skin"]))
    # 侧脸轮廓线（右侧为面向侧，勾线略重）
    d.line([(S(cx - 98), S(348)), (S(cx - 110), S(408)), (S(cx - 102), S(466)),
            (S(cx - 78), S(510)), (S(cx - 36), S(540)), (S(cx + 22), S(548))],
           fill=rgba(C["skin_line"]), width=S(4))
    d.line([(S(cx + 22), S(548)), (S(cx + 76), S(530)), (S(cx + 106), S(488))],
           fill=rgba(C["skin_line"]), width=S(4))

    # --- 耳 ---
    d.ellipse([S(cx - 126), S(418), S(cx - 90), S(472)], fill=rgba(C["skin"]))
    d.ellipse([S(cx - 126), S(418), S(cx - 90), S(472)], outline=rgba(C["skin_line"]), width=S(3))
    d.line([(S(cx - 114), S(438)), (S(cx - 104), S(456))], fill=rgba(C["skin_line"], 170), width=S(2))

    # --- 眉（低平、英气） ---
    # 眉：细长弧形（条漫勾线）
    d.line([(S(cx + 30), S(424)), (S(cx + 64), S(414)), (S(cx + 96), S(416))],
           fill=rgba(C["hair"]), width=S(6), joint="curve")
    d.line([(S(cx - 40), S(426)), (S(cx - 12), S(416)), (S(cx + 12), S(418))],
           fill=rgba(C["hair"]), width=S(6), joint="curve")
    # --- 眼（条漫风：上睑粗线 + 虹膜） ---
    return L


# 眼/嘴区域（超采样前坐标，用于局部重绘框）
EYE_BOX = (ANCHOR["cx"] - 50, 430, ANCHOR["cx"] + 124, 494)   # 双眼区域
MOUTH_BOX = (ANCHOR["cx"] - 14, 500, ANCHOR["cx"] + 116, 572)   # 嘴部区域


def draw_eyes(gaze_x=0.0, gaze_y=0.0, blink=0.0):
    """局部重绘的眼睛层：眼型固定，仅虹膜/瞳孔微移 + 眨眼
    gaze_x/gaze_y: -1~1 归一化偏移；blink: 0~1（1=闭眼）
    """
    L = new_layer()
    d = ImageDraw.Draw(L)
    cx = ANCHOR["cx"]

    for (lx0, lx1, ly, flip) in ((cx + 40, cx + 104, 458, 1), (cx - 30, cx + 30, 460, -1)):
        w = lx1 - lx0
        h = 26
        # 眼白
        d.ellipse([S(lx0), S(ly - h / 2), S(lx1), S(ly + h / 2)], fill=rgba(C["eye_white"]))
        if blink > 0.15:
            # 闭合：上睑线压下
            d.line([(S(lx0 + 2), S(ly - 2 + blink * 4)), (S(lx1 - 2), S(ly - 2 + blink * 4))],
                   fill=rgba(C["hair_line"]), width=S(6))
            continue
        # 虹膜
        icx = lx0 + w * 0.54 + gaze_x * w * 0.10
        icy = ly + gaze_y * 7
        ir = 12.5
        d.ellipse([S(icx - ir), S(icy - ir), S(icx + ir), S(icy + ir)], fill=rgba(C["iris"]))
        d.ellipse([S(icx - ir), S(icy - ir), S(icx + ir), S(icy + ir)],
                  outline=rgba(C["iris_dk"]), width=S(2))
        d.ellipse([S(icx - 6), S(icy - 6), S(icx + 6), S(icy + 6)], fill=rgba(C["pupil"]))
        # 高光
        d.ellipse([S(icx + 3), S(icy - 11), S(icx + 10), S(icy - 4)], fill=(255, 255, 255, 235))
        d.ellipse([S(icx - 10), S(icy + 4), S(icx - 5), S(icy + 9)], fill=(255, 255, 255, 150))
        # 上睑（粗勾线）+ 睫毛
        d.arc([S(lx0), S(ly - h / 2), S(lx1), S(ly + h / 2)], 190, 350,
              fill=rgba(C["hair_line"]), width=S(7))
        d.line([(S(lx1 - 4), S(ly - 12)), (S(lx1 + 10 * flip), S(ly - 20))],
               fill=rgba(C["hair_line"]), width=S(5))
        # 下睑（细线）
        d.arc([S(lx0 + 2), S(ly - h / 2 + 3), S(lx1 - 2), S(ly + h / 2 - 3)], 20, 160,
              fill=rgba(C["skin_line"]), width=S(3))
    # 卧蚕 / 眼下阴影
    d.line([(S(cx + 48), S(478)), (S(cx + 100), S(476))], fill=rgba(C["skin_sh"], 130), width=S(3))
    d.line([(S(cx - 22), S(480)), (S(cx + 24), S(478))], fill=rgba(C["skin_sh"], 130), width=S(3))
    # 鼻（3/4 侧：鼻梁短线 + 鼻头影）
    d.line([(S(cx + 100), S(486)), (S(cx + 94), S(506)), (S(cx + 74), S(512))],
           fill=rgba(C["skin_line"], 200), width=S(3))
    d.line([(S(cx + 92), S(494)), (S(cx + 78), S(508))], fill=rgba(C["skin_sh"], 120), width=S(3))
    return L


def draw_mouth(open_amt=0.0):
    """局部重绘的嘴层：open_amt 0~1 决定开合幅度（说话感）
    下颚线保持不动，仅唇间区域变化 → 不产生面部扭曲
    """
    L = new_layer()
    d = ImageDraw.Draw(L)
    cx = ANCHOR["cx"]
    mx, my = cx + 56, 528

    if open_amt < 0.06:
        # 闭合：一条柔和唇线
        d.line([(S(mx - 34), S(my)), (S(mx - 6), S(my + 3)), (S(mx + 26), S(my - 1))],
               fill=rgba(C["mouth_dk"]), width=S(5))
        d.line([(S(mx - 30), S(my + 5)), (S(mx + 22), S(my + 4))],
               fill=rgba(C["skin_sh"], 170), width=S(3))
        return L

    oh = 4 + open_amt * 13          # 张口高度
    ow = 30
    # 口腔内部
    d.polygon([
        (S(mx - ow), S(my - 2)), (S(mx - 4), S(my + 1)), (S(mx + ow - 2), S(my - 3)),
        (S(mx + ow - 6), S(my + oh)), (S(mx - 2), S(my + oh + 3)), (S(mx - ow + 2), S(my + oh - 2)),
    ], fill=rgba(C["mouth_in"]))
    # 上齿（条漫常用）
    if open_amt > 0.3:
        d.polygon([(S(mx - ow + 2), S(my - 2)), (S(mx + ow - 4), S(my - 3)),
                   (S(mx + ow - 6), S(my + 3)), (S(mx - ow + 4), S(my + 4))], fill=rgba(C["teeth"]))
    # 下唇
    d.line([(S(mx - ow + 2), S(my + oh - 1)), (S(mx - 2), S(my + oh + 3)),
            (S(mx + ow - 6), S(my + oh))], fill=rgba(C["mouth_dk"]), width=S(4))
    # 上唇线
    d.line([(S(mx - ow), S(my - 2)), (S(mx - 4), S(my + 1)), (S(mx + ow - 2), S(my - 3))],
           fill=rgba(C["mouth_dk"]), width=S(4))
    # 下唇高光
    d.line([(S(mx - 16), S(my + oh + 7)), (S(mx + 12), S(my + oh + 6))],
           fill=rgba((250, 232, 224), 150), width=S(3))
    return L


# ============================================================
# 头发（前层：刘海，压在脸上）
# ============================================================
def draw_hair_front():
    L = new_layer()
    d = ImageDraw.Draw(L)
    cx = ANCHOR["cx"]
    # 颅顶
    d.ellipse([S(cx - 124), S(292), S(cx + 124), S(440)], fill=rgba(C["hair"]))
    d.polygon([
        (S(cx - 124), S(366)), (S(cx - 138), S(330)), (S(cx - 118), S(296)),
        (S(cx - 70), S(274)), (S(cx - 6), S(266)), (S(cx + 62), S(276)),
        (S(cx + 112), S(302)), (S(cx + 130), S(340)), (S(cx + 120), S(372)),
    ], fill=rgba(C["hair"]))
    # 刘海（右侧斜分缝，露出右侧脸轮廓 → 3/4 侧脸感）
    # 刘海：左侧厚、右侧斜分，露出右侧面部轮廓
    d.polygon([
        (S(cx - 122), S(352)), (S(cx - 86), S(314)), (S(cx - 30), S(336)),
        (S(cx + 16), S(312)), (S(cx + 62), S(330)), (S(cx + 104), S(350)),
        (S(cx + 122), S(372)), (S(cx + 100), S(392)), (S(cx + 56), S(374)),
        (S(cx + 8), S(390)), (S(cx - 44), S(374)), (S(cx - 96), S(392)),
    ], fill=rgba(C["hair"]))
    # 发丝（条漫勾线）
    # 发丝高光：沿颅顶与刘海走向的弧线（条漫常用，避免直线"划痕"感）
    d.arc([S(cx - 100), S(306), S(cx - 6), S(392)], 250, 340,
          fill=rgba(C["hair_hl"], 110), width=S(4))
    d.arc([S(cx - 66), S(292), S(cx + 66), S(384)], 250, 335,
          fill=rgba(C["hair_hl"], 90), width=S(3))
    d.arc([S(cx + 30), S(302), S(cx + 118), S(388)], 250, 330,
          fill=rgba(C["hair_hl"], 80), width=S(3))
    # 鬓发挑染
    d.line([(S(cx - 128), S(392)), (S(cx - 136), S(500))], fill=rgba(C["hair_hl"], 70), width=S(3))
    d.line([(S(cx + 128), S(390)), (S(cx + 134), S(506))], fill=rgba(C["hair_hl"], 70), width=S(3))
    # 鬓发（右侧贴近脸）
    d.polygon([(S(cx + 106), S(364)), (S(cx + 144), S(408)), (S(cx + 132), S(480)),
               (S(cx + 102), S(440))], fill=rgba(C["hair"]))
    d.polygon([(S(cx - 122), S(358)), (S(cx - 150), S(418)), (S(cx - 140), S(520)),
               (S(cx - 108), S(452))], fill=rgba(C["hair"]))
    # 颅顶高光
    hl = new_layer()
    hd = ImageDraw.Draw(hl)
    hd.arc([S(cx - 88), S(306), S(cx + 80), S(408)], 205, 320, fill=(255, 255, 255, 46), width=S(15))
    hl = hl.filter(ImageFilter.GaussianBlur(S(5)))
    L = Image.alpha_composite(L, hl)
    return L
