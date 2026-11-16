🇯🇵 日本語 | [🇺🇸 English](README.en.md)

# スキル（AI エージェントに読ませる手順書）

この実験で AI に使わせた作業手順を、特定の環境に依存しない形にまとめたものです。
Claude Code・Codex・Hermes Agent など、どのエージェントでも「このファイルを読んでから作業して」と渡せば使えます。

| ファイル | 使う場面 |
| --- | --- |
| [input-comparison-experiment.md](input-comparison-experiment.md) | この実験そのもの（絵だけ vs 絵＋図面）を公平に回す・採点する |
| [image-to-massing.md](image-to-massing.md) | 外観の絵（AI 画像・写真）から Rhino のボリューム模型を起こす |
| [figma-drawing-markup-loop.md](figma-drawing-markup-loop.md) | AI が図面案を Figma に置き、人がペンで描き込み、AI が次の版を描く往復 |
| [pbr-texture-pipeline.md](pbr-texture-pipeline.md) | 画像生成 AI で素材の色を作り、法線・粗さ・AO まで揃える（リピート感を消すコツ込み） |

## 使い方
- エージェントの「スキル」機能がある場合（Claude Code の skills、Hermes の skills など）は、そのフォルダに置く。
- 無い場合は、指示の最初に「`skills/image-to-massing.md` を読んでから作業してください」と書く。
- **A・B の比較を回すときは、作らせる側の AI にはスキルを渡さない**（条件が変わる）。スキルは、準備・採点・図面づくりをする側の AI に渡す。

## 注意
- 書いてあるツール名（`execute_rhino_code`、Figma の `use_figma` など）は、接続の仕方によって名前が違います。自分の環境の同じ働きのツールに読み替えてください。
- 2026年11月時点の AI（Claude Opus 5.5）で確かめた手順です。
