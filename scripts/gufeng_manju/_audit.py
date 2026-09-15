import sys, os
sys.path.insert(0,'.')
import numpy as np
from PIL import Image
import render as R
from render import compose
from scene import draw_background, draw_desk
bg_base = Image.alpha_composite(draw_background(), draw_desk())
head_img = R.draw_head(); hb = R.draw_hair_back(); hf = R.draw_hair_front()
out = {}
for f in range(120):
    out[f] = np.asarray(compose(f, bg_base, head_img, hb, hf).convert('RGB'), dtype=np.int16)
base = out[0]
print('=== pre-zoom pure micro-motion sequence (ground truth) ===')
diffs = np.array([float(np.abs(out[f+1]-out[f]).mean()) for f in range(119)])
print('adjacent diff  mean=%.4f max=%.4f' % (diffs.mean(), diffs.max()))
print('diff jerk      max=%.4f' % np.abs(np.diff(diffs)).max())
print('first vs last  mean|d|=%.4f' % np.abs(out[119]-base).mean())
Rig = np.stack([out[f][500:640, 560:780] for f in range(120)], axis=0)
print('face rigid region cross-frame std=%.4f' % Rig.std(axis=0).mean())
Wl = np.stack([out[f][200:420, 900:1300] for f in range(120)], axis=0)
print('background wall cross-frame std=%.4f' % Wl.std(axis=0).mean())
