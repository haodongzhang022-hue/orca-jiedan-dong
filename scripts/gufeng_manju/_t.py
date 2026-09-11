from scene import *
from character import *
bg = draw_background(); desk = draw_desk()
c = Image.alpha_composite(bg, draw_body(breath=0.0, sway=0.0))
c = Image.alpha_composite(c, draw_hair_back())
c = Image.alpha_composite(c, draw_head())
c = Image.alpha_composite(c, draw_eyes(gaze_x=0.3, gaze_y=0.1))
c = Image.alpha_composite(c, draw_mouth(open_amt=0.5))
c = Image.alpha_composite(c, draw_hair_front())
c = Image.alpha_composite(c, desk)
c = add_light_beams(c)
c.resize((W,H), Image.LANCZOS).convert("RGB").save("/tmp/char_test.png")
print("ok")
