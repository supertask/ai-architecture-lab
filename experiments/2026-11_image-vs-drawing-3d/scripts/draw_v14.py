# 公開用の写し：inputs/drawing_v14.png を描いたスクリプト（B に渡した図面の元）。
# 実行：uv run -q --with pillow python scripts/draw_v14.py → work/drawing/v14_sheet.png
# 先頭のコメントは、人の描き込み（Figma の r1〜r9）を AI がどう読んで反映したかの記録。
# 注意：A・B の実験中、AI にはこのファイルを見せていない（見せると B が図面の数値を直接読めてしまう）。
# v14：人の描き込み r9（v13 への描き込み）を反映 — 左の柱と凹みの上の屋根を前へ 1m（y=2.0→1.0m）。スリットも 1m 前へ（y 2.4〜3.7→1.4〜2.7m）。左側面も 7.5m の左の箱が y=1.0m まで
# v13：人の描き込み r7（v12 への描き込み）を反映
#  - 凹みの奥を 3.5m → 5.0m（1階・2階）
#  - 左の箱の左前の壁（x0〜1m）を y=2.0m まで下げる（その前は凹みとつながる）
#  - 左側面のスリットを y 2.4〜3.7m にずらす
#  - 右の塊の前の左角の出っ張り（x6〜7m）の奥側を y=-0.9 → -0.5m
#  - 上の屋根（緑）：凹みの上は y=2.0m より奥と x6〜7m。厚みは正面の黄色（左の箱の上の帯）
#  - 前の左角の出っ張りは残す（描いた人 2026-11-04「出っ張りですね」）。前の左角の丸み（R0.5）を正面・側面に縦の細線で表す
#  - 右の箱は全部 6.8m（描いた人 r8・案C 2026-11-04）。左の箱の上の帯（6.8〜7.5m）は y=2m より奥だけ。前 2m は右の箱だけで、左側面に帯は出ない
#  - 正面：車庫の上の 3.3m の線＝2階の右前の丸み（R1.5）の下に見える1階の屋根の縁（描いた人の説明）。丸みは縦の細線で表す
#  - 正面：黄色＝左の箱（左の柱＋上の帯 x0〜12.6m、帯は y=2m より奥）、それ以外＝右の箱（6.8m）。帯の下端は x0〜6m が 5.8m、x6〜12.6m が 6.8m
# v12：人の描き込み r6（v11 への描き込み）を反映
#  - 右の塊の前の左角を 1m 凹み側へ出す（x 6〜7m、前の角 R0.5）。1階・2階とも
#  - 右の塊の x 7〜12.6m を 7.5m に上げる（左の箱と同じ高さ、境目の線は消す）
#  - 凹みの天井を 6.8m → 5.8m に下げる
#  - 左側面のスリットの上端を 7.2m → 5.8m（凹みの天井とそろえる。上は「いらない」＝コンクリート）
#  - 1階の屋根の線を左へ延ばした短い線（x 14.4〜15.3m）は意味を確認中（①）
# v11：人の描き込み r5（v10 への描き込み）を反映
#  - 側面：スリットの上端は 7.2m まで（その上 7.2〜7.5m はコンクリート）
#  - 正面：2階の右上の角（x=15.3m）は直角
# v10：人の描き込み r4（v9 への描き込み）を反映
#  - 凹みの奥を 4.0m→3.5m（1階・2階）
#  - 車庫の左の前の角を丸める
#  - 2階は x=15.3m まで（その右 15.3〜18m は1階だけ＝屋根）。2階の前の角を丸める
#  - 左の箱を 7.5m に上げ、スリットを上端まで抜く（側面の赤い括弧）
# 以下は v9 の説明
#  - 車庫：x 12.6〜17.3m、奥行き 8.6m まで。車2台を縦に並べる。道路側は開口（x=15m の線と車庫の奥の線は削除）
#  - 右の塊の右奥の角を丸める
#  - 平面は 1階 と 2階 の2枚。正面は 1階平面の真下、左側面は 1階平面の右（奥行きをそろえる）、2階平面は正面の下（x をそろえる）
from PIL import Image, ImageDraw, ImageFont
import math
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'drawing') + '/'
os.makedirs(OUT, exist_ok=True)
from fontutil import font as _font
FT = lambda s: _font(s, bold=False)
CONF = (215, 215, 215); DARK = (195, 195, 195); WIN = (60, 165, 230); INK = (25, 25, 25)
Q = (220, 30, 30); PROJ = (120, 170, 220)
DEP, R_BACK, SW, REC_Y, GX, YF, R_FL = 9300, 2000, 1000, 5000, 7000, -1800, 900
R_GF = 1300            # 車庫の左の前の角
X2, R_2F = 15300, 1500  # 2階の右端と前の角
H_1F = 3300            # 1階だけの部分の高さ
G0, G1, GB, R_G = 12600, 17300, 8600, 650      # 車庫（内側）
BX1, R_BR = 18000, 1200                         # 右端、右奥の角の丸み
H_L, H_R, H_REC, H_CP, R_TOP = 7500, 6800, 5800, 2700, 0
SLIT_TOP = 5800
PIER_Y, EXT_TOP, SL0, SL1 = 1000, -500, 1400, 2700
X_HI, EX, R_EX = 12600, 6000, 500   # 7.5m に上げる範囲の右端、凹み側へ出した前の角
k = 0.05; PX0 = 140
P1_Y0 = 760; FRONT_Z0 = 1500; P2_Y0 = 2240
SIDE_Z0 = PX0 + k * BX1 + 260
W, H = int(SIDE_Z0 + k * H_L + 260), 2480
im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
def PPf(y0): return lambda x, y: (PX0 + k * x, y0 - k * y)
P1, P2 = PPf(P1_Y0), PPf(P2_Y0)
PF = lambda x, z: (PX0 + k * x, FRONT_Z0 - k * z)
PS = lambda y, z: (SIDE_Z0 + k * z, P1_Y0 - k * y)
def R(a, b): return [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
def arc(cx, cy, r, a0, a1, n=24): return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
def dash(p, q, col=PROJ, w=1, seg=10, gap=8):
    (x0, y0), (x1, y1) = p, q; L = math.hypot(x1 - x0, y1 - y0); t = 0
    while t < L:
        a = t / L; b = min(L, t + seg) / L
        d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=col, width=w); t += seg + gap
def qmark(x, y, n):
    d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=Q, outline='white', width=3); d.text((x - 9, y - 18), str(n), fill='white', font=FT(26))
OUTLINE = [(0, PIER_Y), (SW, PIER_Y), (SW, REC_Y), (GX, REC_Y), (GX, EXT_TOP), (EX, EXT_TOP)] + arc(EX + R_EX, YF + R_EX, R_EX, 180, 270)
OUTLINE2 = OUTLINE + [(X2 - R_2F, YF)] + arc(X2 - R_2F, YF + R_2F, R_2F, -90, 0)[1:] + arc(X2 - R_2F, DEP - R_2F, R_2F, 0, 90) + arc(R_BACK, DEP - R_BACK, R_BACK, 90, 180)
OUTLINE += [(BX1, YF)] + arc(BX1 - R_BR, DEP - R_BR, R_BR, 0, 90) + arc(R_BACK, DEP - R_BACK, R_BACK, 90, 180)
GARAGE = [(G0 - R_GF, YF)] + arc(G0 - R_GF, YF + R_GF, R_GF, -90, 0)[1:] + [(G0, GB - R_G)] + arc(G0 + R_G, GB - R_G, R_G, 180, 90)[1:] + [(G1 - R_G, GB)] + arc(G1 - R_G, GB - R_G, R_G, 90, 0)[1:] + [(G1, YF)]
def grid(P):
    for xm in range(-1, 20): d.line([P(xm * 1000, -3000), P(xm * 1000, 10000)], fill=(240, 240, 240))
    for ym in range(-3, 11): d.line([P(-1000, ym * 1000), P(19000, ym * 1000)], fill=(240, 240, 240))
def plan(P, floor):
    grid(P)
    if floor == 2:
        d.polygon([P(*p) for p in OUTLINE], fill=(240, 240, 240)); d.line([P(*p) for p in OUTLINE] + [P(0, PIER_Y)], fill=(160, 160, 160), width=1)
    OL = OUTLINE if floor == 1 else OUTLINE2
    d.polygon([P(*p) for p in OL], fill=CONF)
    d.line([P(*p) for p in OL] + [P(0, PIER_Y)], fill=INK, width=3)
    d.line([P(0, SL0), P(0, SL1)], fill=WIN, width=7)
    d.line([P(GX, EXT_TOP), P(GX, REC_Y)], fill=WIN, width=7)
    if floor == 1:
        d.polygon([P(*p) for p in GARAGE], fill=(250, 250, 250))
        d.line([P(*p) for p in GARAGE], fill=INK, width=3)
        for (y0, y1) in ((-1300, 3300), (3700, 8300)):
            d.rounded_rectangle(R(P(14050, y1), P(15850, y0)), 5, outline=(120, 120, 120), width=2)
            d.text(P(14700, (y0 + y1) / 2 + 300), '車', fill=INK, font=FT(24))
        d.polygon([P(14950, -1900), P(14700, -2300), P(15200, -2300)], fill=INK); d.line([P(14950, -2300), P(14950, -3200)], fill=INK, width=3)
        d.text(P(15400, -2000), '←車庫の入口', fill=INK, font=FT(20))
        d.text(P(G0 + 300, 9100), '車庫（2台・縦）', fill=INK, font=FT(18))
        for t, x, y, s in (('左の箱', 2500, 7000, 26), ('凹み', 2900, 1600, 24), ('右の塊', 8800, 5000, 26), ('ガラス', GX + 150, 1000, 20)):
            d.text(P(x, y), t, fill=INK, font=FT(s))
        d.text(P(-1000, 10300), '1階 平面', fill=INK, font=FT(26))
    else:
        def hatch(x0, y0, x1, y1):
            for c in range(int(-(y1 - y0)), int(x1 - x0), 600):
                ax, ay = x0 + max(0, c), y0 + max(0, -c)
                bx = min(x1, x0 + c + (y1 - y0)); by = y0 + (bx - x0 - c)
                dash(P(ax, ay), P(bx, by), col=(175, 175, 175))
        hatch(SW, PIER_Y, GX, REC_Y); hatch(EX, EXT_TOP, GX, PIER_Y)
        GR = (40, 170, 70)
        d.line([P(0, PIER_Y), P(EX, PIER_Y), P(EX, EXT_TOP)], fill=GR, width=5)
        d.rectangle(R(P(1600, 750), P(5600, -250)), fill='white'); d.text(P(1700, 600), '凹み（上は空）', fill=INK, font=FT(20))
        d.rectangle(R(P(1200, 3500), P(5900, 2800)), fill='white'); d.text(P(1300, 3400), '凹み（吹抜け・上に屋根）', fill=INK, font=FT(18))
        d.text(P(200, -1300), '緑＝上の屋根の端', fill=GR, font=FT(16))
        for i in range(len(GARAGE) - 1):
            dash(P(*GARAGE[i]), P(*GARAGE[i + 1]), seg=6, gap=6)
        d.text(P(G0 + 300, 3000), '車庫の上', fill=INK, font=FT(20))
        d.text(P(X2 + 250, 6500), '1階の屋根', fill=INK, font=FT(18))
        for t, x, y, s in (('左の箱', 2500, 7000, 26), ('右の塊', 8800, 5000, 26)):
            d.text(P(x, y), t, fill=INK, font=FT(s))
        d.text(P(-1000, 10300), '2階 平面（破線＝下の車庫、薄い灰＝1階だけの部分）', fill=INK, font=FT(26))
    d.line([P(-1000, -2800), P(19000, -2800)], fill=(150, 150, 150), width=2)
    d.text(P(3500, -3000), '道路', fill=INK, font=FT(22))
for x in (0, SW, EX, GX, X_HI, G0, X2, G1, BX1):
    dash(P1(x, -3200), PF(x, H_L + 500)); dash(PF(x, -600), P2(x, 9800))
for y in (DEP, REC_Y, PIER_Y, 0, EXT_TOP, YF):
    dash(P1(BX1 + 400, y), PS(y, -400))
plan(P1, 1); plan(P2, 2)
# 2階の帯窓（外観 C 案、2026-11-04）：右の箱の前面 x=7.1m から、右前の丸い角（R1.5）を回り込む。高さ 4.7〜5.9m（仮）
RIB0, RIB_Z0, RIB_Z1 = EX + R_EX + 600, 4700, 5900
d.line([P2(RIB0, YF), P2(X2 - R_2F, YF)] , fill=WIN, width=9)
d.line([P2(*q) for q in arc(X2 - R_2F, YF + R_2F, R_2F, -90, 0)], fill=WIN, width=9)
d.line([P1(2400, DEP), P1(6800, DEP)], fill=WIN, width=9); d.text(P1(2600, DEP + 650), '裏：掃き出し窓（1階 LDK）', fill=WIN, font=FT(16))
d.line([P2(8000, DEP), P2(12000, DEP)], fill=WIN, width=9); d.text(P2(5600, DEP - 900), '裏：帯窓（2階、正面と同じ高さ）', fill=WIN, font=FT(16))
d.text(P2(RIB0 + 1200, YF + 1000), '帯窓（2階・丸い角まで回る）', fill=WIN, font=FT(18))
d.text((30, 14), 'v14（r9 を反映＋窓：正面の帯窓・裏の2か所）　1階平面＋正面（真下）＋左側面（右）＋2階平面（下）　1マス＝1m', fill=INK, font=FT(28))
d.text((30, 54), '灰＝コンクリート（正面の黄みの灰＝左の箱）　水色＝窓　緑＝上の屋根の端　赤い番号＝確認したい所', fill=INK, font=FT(20))
d.line([PF(-1000, 0), PF(19000, 0)], fill=INK, width=3)
LB = (222, 214, 190)
rb = [(EX, 0), (EX, H_R), (X2, H_R), (X2, H_1F), (BX1, H_1F), (BX1, 0)]
d.polygon([PF(*p) for p in rb], fill=CONF); d.line([PF(*p) for p in rb], fill=INK, width=3)
d.rectangle(R(PF(SW, 0), PF(EX, H_REC)), fill=DARK, outline=INK, width=2)
lb = [(0, 0), (0, H_L), (X_HI, H_L), (X_HI, H_R), (EX, H_R), (EX, H_REC), (SW, H_REC), (SW, 0)]
d.polygon([PF(*p) for p in lb], fill=LB); d.line([PF(*p) for p in lb] + [PF(0, 0)], fill=INK, width=3)
d.text(PF(8000, H_L - 600), '左の箱（上の帯・奥）', fill=INK, font=FT(14)); d.text(PF(GX + 2000, 3000), '右の箱', fill=INK, font=FT(22))
# 前の左角の出っ張り（x6〜7m）は残す。前の左角は丸い（R0.5、平面）→ 縦の細線で丸みを表す
for i in range(1, 6):
    xx = EX + R_EX * (1 - math.sin(math.radians(90 * i / 6)))
    d.line([PF(xx, 0), PF(xx, H_R)], fill=(170, 170, 170), width=1)
d.line([PF(EX + R_EX, 0), PF(EX + R_EX, H_R)], fill=(120, 120, 120), width=1)
d.text(PF(EX - 1200, 2600), '丸み→', fill=INK, font=FT(14))
# 2階の右前の角は丸い（R1.5、平面）。1階は四角なので、丸みの下に1階の屋根の縁が見える
for i in range(1, 6):
    xx = X2 - R_2F + R_2F * math.sin(math.radians(90 * i / 6))
    d.line([PF(xx, H_1F), PF(xx, H_R)], fill=(170, 170, 170), width=1)
d.line([PF(X2 - R_2F, H_1F), PF(X2 - R_2F, H_R)], fill=(120, 120, 120), width=1)
d.line([PF(X2 - R_2F, H_1F), PF(X2, H_1F)], fill=INK, width=3)
d.text(PF(X2 - R_2F - 1100, H_R - 900), '丸み→', fill=INK, font=FT(14)); d.text(PF(X2 + 300, H_1F + 400), '1階の屋根の縁', fill=INK, font=FT(14))
d.rectangle(R(PF(G0, 0), PF(G1, H_CP)), fill='white', outline=INK, width=3)
d.rectangle(R(PF(RIB0, RIB_Z0), PF(X2, RIB_Z1)), fill=WIN, outline=INK, width=1)
for xx in (9400, 11700, X2 - R_2F):
    d.line([PF(xx, RIB_Z0), PF(xx, RIB_Z1)], fill=INK, width=1)
d.text(PF(RIB0 + 200, RIB_Z0 - 650), '帯窓 4.7〜5.9m（右端は丸い角を回る）', fill=INK, font=FT(14))
d.text(PF(G0 + 1700, 1300), '車庫', fill=INK, font=FT(20))
d.text(PF(SW + 300, H_REC - 900), '凹みの奥の壁（5.0m奥）', fill=INK, font=FT(18)); d.text(PF(SW + 300, H_REC + 650), '凹みの天井 5.8m', fill=INK, font=FT(16))
d.text(PF(-2600, H_L + 400), '7.5m', fill=INK, font=FT(18)); d.text(PF(3500, H_L + 450), '7.5m（左の箱の上の帯 〜12.6m）', fill=INK, font=FT(16)); d.text(PF(X_HI + 700, H_R + 750), '6.8m（右の箱）', fill=INK, font=FT(18)); d.text(PF(X2 + 300, H_1F + 900), '3.3m（1階だけ）', fill=INK, font=FT(16))
d.text(PF(1500, -900), '正面（道路側から）', fill=INK, font=FT(24))
d.line([PS(10000, 0), PS(-2800, 0)], fill=INK, width=3)
d.rectangle(R(PS(YF, 0), PS(PIER_Y, H_R)), fill=DARK, outline=INK, width=2)
for i in range(1, 6):
    yy = YF + R_EX * (1 - math.sin(math.radians(90 * i / 6)))
    d.line([PS(yy, 0), PS(yy, H_R)], fill=(120, 120, 120), width=1)
d.rectangle(R(PS(PIER_Y, 0), PS(DEP, H_L)), fill=CONF, outline=INK, width=3)
d.line([PS(DEP - R_BACK, 0), PS(DEP - R_BACK, H_L)], fill=(140, 140, 140), width=1)
d.rectangle(R(PS(SL0, 300), PS(SL1, SLIT_TOP)), fill=WIN, outline=INK, width=1)
d.text(PS(6200, 1500), '左の箱', fill=INK, font=FT(22)); d.text(PS(DEP - 1300, 1500), '丸み', fill=INK, font=FT(18))
d.text(PS(-300, 2500), '右の箱', fill=INK, font=FT(16))
d.text(PS(10700, 0), '左側面（スリットの面）', fill=INK, font=FT(24))
d.text(PS(-2600, -1400), '地面', fill=INK, font=FT(16)); d.text(PS(-2600, H_L - 2000), '高さ→', fill=INK, font=FT(16))
im.save(OUT + 'v14_sheet.png'); print(im.size)
