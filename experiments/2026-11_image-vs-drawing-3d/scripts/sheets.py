# 投稿・Notion 用の比較シート
from PIL import Image, ImageDraw, ImageFont
import os
D = os.path.dirname(os.path.abspath(__file__)) + '/'
B = D + '../'
F = lambda s: ImageFont.truetype('C:/Windows/Fonts/meiryob.ttc', s)
def tile(path, label, w=800, h=450, sub=None):
    c = Image.new('RGB', (w, h + 60), 'white'); im = Image.open(path).convert('RGB').resize((w, h)); c.paste(im, (0, 60))
    dr = ImageDraw.Draw(c); dr.text((12, 10), label, fill='black', font=F(28))
    if sub: dr.text((w - 12 - dr.textlength(sub, font=F(22)), 16), sub, fill=(90, 90, 90), font=F(22))
    return c
def grid(tiles, cols, title, out):
    w, h = tiles[0].size; rows = (len(tiles) + cols - 1) // cols
    S = Image.new('RGB', (w * cols, h * rows + 70), 'white'); dr = ImageDraw.Draw(S); dr.text((14, 16), title, fill='black', font=F(32))
    for i, t in enumerate(tiles): S.paste(t, ((i % cols) * w, 70 + (i // cols) * h))
    S.save(D + out, quality=90); print(out, S.size)
A, Bd, C = D + 'A_image_only/', D + 'B_image_plus_drawing/', D + 'C_reference_v14/'
grid([tile(B + '../../../../proposals/images/P-20261031-02-house-v6C.png' if False else '<KIT>/inputs/house_v6C.png', '元の外観 v6C（AI画像）'),
      tile(C + 'eye_concrete.png', '正解：図面どおりの模型 v14'),
      tile(A + 'eye_concrete.png', 'A　外観だけでAIが作った模型'),
      tile(Bd + 'eye_concrete.png', 'B　外観＋Figmaの図面で作った模型')], 2,
     '同じカメラで撮った比較（正面側）', 'cmp_front.jpg')
grid([tile(C + 'back.png', '正解 v14：裏・右から'), tile(C + 'back_left.png', '正解 v14：裏・左から'),
      tile(A + 'back.png', 'A 外観だけ：裏・右から'), tile(A + 'back_left.png', 'A 外観だけ：裏・左から'),
      tile(Bd + 'back.png', 'B 外観＋図面：裏・右から'), tile(Bd + 'back_left.png', 'B 外観＋図面：裏・左から')], 2,
     '見えない裏側の比較（外観の画像には写っていない面）', 'cmp_back.jpg')
grid([tile(Bd + 'eye_concrete.png', '打放し（型枠・Pコン）'), tile(Bd + 'eye_black_mortar.png', '黒モルタル'),
      tile(Bd + 'eye_rammed_earth.png', '版築')], 3, 'B（外観＋図面）の模型に、テクスチャ3種', 'textures_B.jpg')
grid([tile(A + 'axo.png', 'A 外観だけ'), tile(Bd + 'axo.png', 'B 外観＋図面'), tile(C + 'axo.png', '正解 v14')], 3,
     '斜め上から（平行投影）', 'cmp_axo.jpg')
# テクスチャ付きの比較（行＝A・B・正解、列＝打放し・黒モルタル・版築）
T = [('concrete', '打放し'), ('black_mortar', '黒モルタル'), ('rammed_earth', '版築')]
tl = []
for folder, jp in ((A, 'A 外観だけ'), (Bd, 'B 外観＋図面'), (C, '正解 v14')):
    for k, tj in T: tl.append(tile(folder + 'eye_%s.png' % k, jp, sub=tj))
grid(tl, 3, '同じカメラ・同じテクスチャで比較（行：A／B／正解　列：打放し／黒モルタル／版築）', 'cmp_textures.jpg')
grid([tile('<KIT>/inputs/house_v6C.png', '元の外観 v6C（AI画像）'),
      tile(C + 'eye_rammed_earth.png', '正解：図面どおりの模型 v14', sub='版築'),
      tile(A + 'eye_rammed_earth.png', 'A　外観だけでAIが作った模型', sub='版築'),
      tile(Bd + 'eye_rammed_earth.png', 'B　外観＋Figmaの図面で作った模型', sub='版築')], 2,
     '同じカメラで撮った比較（正面側・テクスチャ付き）', 'cmp_front_tex.jpg')
# 外観 v6 に寄せたグレーの打放し（concrete_v6、14.4m 角でリピートなし）
grid([tile('<KIT>/inputs/house_v6C.png', '元の外観 v6C（AI画像）'),
      tile(C + 'eye_concrete_v6.png', '正解：図面どおりの模型 v14', sub='打放し（v6に寄せたグレー）'),
      tile(A + 'eye_concrete_v6.png', 'A　外観だけでAIが作った模型', sub='打放し（v6に寄せたグレー）'),
      tile(Bd + 'eye_concrete_v6.png', 'B　外観＋Figmaの図面で作った模型', sub='打放し（v6に寄せたグレー）')], 2,
     '同じカメラで撮った比較（正面側・テクスチャ付き）', 'cmp_front_v6grey.jpg')
