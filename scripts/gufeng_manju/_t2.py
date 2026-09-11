import sys, os
sys.path.insert(0,'/workspace/scripts/gufeng_manju'); os.chdir('/workspace/scripts/gufeng_manju')
from PIL import Image
from scene import *
from character import *
bg = draw_background(); desk = draw_desk()
c = Image.alpha_composite(bg, draw_body(0.0, 0.0))
c = Image.alpha_composite(c, draw_hair_back())
c = Image.alpha_composite(c, draw_head())
c = Image.alpha_composite(c, draw_eyes(0.3, 0.1, 0.0))
c = Image.alpha_composite(c, draw_mouth(0.6))
c = Image.alpha_composite(c, draw_hair_front())
c = Image.alpha_composite(c, desk)
c = add_light_beams(c)
c.resize((W,H), Image.LANCZOS).convert("RGB").save("/tmp/char_test.png")
print("ok")
