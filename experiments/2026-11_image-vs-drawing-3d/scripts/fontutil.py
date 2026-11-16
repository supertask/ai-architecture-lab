# 日本語フォントを OS ごとに探す（Windows の Meiryo → macOS のヒラギノ → Linux の Noto CJK → Pillow 既定）
# 環境変数 KIT_FONT にフォントファイルを指定すれば、それを優先する。
import os
from PIL import ImageFont

_CANDIDATES = {
    True: ['C:/Windows/Fonts/meiryob.ttc', '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
           '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc'],
    False: ['C:/Windows/Fonts/meiryo.ttc', '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc'],
}


def font(size, bold=True):
    paths = ([os.environ['KIT_FONT']] if os.environ.get('KIT_FONT') else []) + _CANDIDATES[bold]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()
