# Unreal Engine 側の準備（家具を Archicad と一緒に動かす）

Archicad の家具を Unreal Engine に映し、どちらで動かしてももう一方が付いてくるようにします。
Archicad → Unreal Engine の形と素材は Datasmith Direct Link、家具の位置の行き来は `ue_follow.py` が受け持ちます。

| ファイル | 役割 |
|---|---|
| `ue_follow.py` | 見張り。Archicad と Unreal Engine の家具の位置を両方向に合わせ続ける |
| `ue_attach.py` | 既製の家具メッシュを Archicad の家具（Datasmith のアクタ）の子として付ける |
| `ue_material_swap.py` | Datasmith が作った素材アセットを自分の素材に差し替える（アセット単位） |
| `ue_mark_dirty.py` | 保存の前に「変更あり」にする |
| `config.json` | Unreal Engine 側の設定（パスは書かない。スクリプトが自分の場所を見つける） |

すべて Unreal Engine エディタの中で動く Python です。ターミナルからは実行しません。

## 1. 初回の準備

1. Archicad に **Datasmith Archicad Exporter**（Epic Games 配布、Direct Link 対応版）を入れる。
2. Unreal Engine 5 で新規プロジェクトを作る（建築テンプレートでも空でもよい）。
3. 編集 → プラグイン で **Python Editor Script Plugin** と **Datasmith Importer** を有効にし、エディタを再起動する。
4. （任意）編集 → プロジェクト設定 → Python で「Developer Mode」を有効にすると、エラーが読みやすくなる。

## 2. Archicad と繋ぐ（Direct Link）

1. Archicad でプロジェクトを開き、ウィンドウ → パレット → Datasmith を出す。
2. Archicad の 3D ウィンドウを前面にする（3D が前の時だけ送られる）。
3. Unreal Engine のツールバーの「＋（クイック追加）」→ Datasmith → Direct Link Import で、Archicad のソースを選んで取り込む。
4. コンテンツブラウザで取り込んだシーンアセットを右クリック →「Direct Link 自動再インポート」を有効にする。
5. Archicad で家具を少し動かし、Unreal Engine に届くか確かめる（Archicad の Datasmith パレットの Sync / AutoSync）。

## 3. 見張りを動かす（ue_follow.py）

1. Archicad に **Tapir アドオン** が入って動いていることを確かめる（キット本体の準備と同じ）。
2. Direct Link で一度同期し、Unreal Engine と Archicad の家具が同じ位置にある状態にする（最初に見た位置で対応を測るため）。
3. Unreal Engine のアウトプットログ下の入力欄を「Cmd」にして `py "<KIT>/ue/ue_follow.py"` と入力する（`<KIT>` はこのキットのフォルダを置いた場所）（ファイル → Python スクリプトを実行 からでもよい）。
4. ログに `ue_follow running: N actors` と出れば動いている。N は Archicad の家具（オブジェクト）の数。
5. Unreal Engine でギズモを掴んで家具を動かすと、Archicad の平面図がドラッグ中から付いてくる（約 0.3 秒ごとにまとめて送信）。
6. Archicad で動かす、または AI エージェントがキットで配置を反映すると、Unreal Engine が約 0.2〜0.4 秒で付いてくる。
7. 止める: `py ".../ue/ue_follow.py" stop`　状態を見る: `py ".../ue/ue_follow.py" status`

毎回の手入力を省くには: 編集 → プロジェクト設定 → プラグイン → Python →「スタートアップスクリプト」に `ue_follow.py` のフルパスを追加する（エディタ起動時に自動で動き、Archicad が後から開いても 5 秒ごとに探す）。

- 対応づけは自動です。Datasmith がアクタに書く Archicad の GUID（`Datasmith_UniqueId`）で引くので、表を作る必要はありません。
- Archicad が複数開いている時は `config.json` の `archicad_port` に番号を書く。
- ログは `ue/logs/follow.jsonl` に出る。
- 実測（2026-11-17、家具 21 点）: Archicad で動かす → Unreal Engine が約 0.6 秒で追従。Unreal Engine でギズモを 2.5 秒ドラッグ → ドラッグ中に 5 回まとめて送信（1 回 0.28〜0.37 秒）し、平面図がドラッグ中から動く。キットの配置反映（17 点）と元に戻す操作 → 全点が付いてきて位置の差 0 cm。
- 動いているか確かめる: `status` で `followed` と `calibrated` が家具の数と同じか。ログに `batch`（ドラッグ中の送信）、`pulled`（Archicad から受けた移動）が出る。

## 4. 本物の家具を付ける（ue_attach.py、任意）

Archicad の家具は箱に近い形で届くので、既製の 3D 家具に見た目だけ差し替えます。動かす対象（Datasmith のアクタ）は変えずに子として付けるので、見張りと Direct Link はそのまま効きます。

1. 家具のメッシュをプロジェクトに取り込む（例: Poly Haven の CC0 家具の FBX）。直立・実寸にしておく。画像から作った 3D は、取り込む前に直立・正面・実寸に直しておく。
2. `config.json` の `attach.items` に「どの家具に」「どのメッシュを」を書く。`match` は `kind`（キット本体の `config.json` の種類名。例 `sofa`）、`libpart`（部品名の一部）、`guid` のどれか。
3. `mesh_front` にメッシュの正面の向きを書く（Poly Haven の多くは `+Y`）。逆を向いたら項目に `"yaw": 180`。
4. `fit` を選ぶ: `none`＝実寸のまま（おすすめ）、`uniform`＝Archicad の箱に平面で収まるよう等倍、`box`＝箱に合わせて各方向に伸縮、`height`＝高さに合わせて等倍（植物）。
5. `py ".../ue/ue_attach.py"` を実行する。子は `LK_<家具名>_<番号>` という名前で付き、元の箱は隠れる。何度流しても同じ結果になる。

## 5. 素材を差し替える（ue_material_swap.py、任意）

1. 自分の素材（マテリアルかマテリアルインスタンス）を作っておく。
2. `config.json` の `material_swap.map` に「自分の素材のパス → Datasmith が作った素材の名前」を書く。
3. `py ".../ue/ue_material_swap.py" check` で当たる素材を確かめてから、`check` を外して実行する。

## 6. 保存

1. `py ".../ue/ue_mark_dirty.py"` を実行し、レベルのタブに `*` が付いたのを確かめる。
2. ファイル → 現在のレベルを保存（または すべて保存）。

## 分かっている落とし穴

| 起きること | 対処 |
|---|---|
| Python で部品のスロットごとに素材を割り当てるループを回すと、数秒〜数分後にエディタが落ちる | 素材はアセット単位で差し替える（`ue_material_swap.py`）。アクタやスロットのループで `set_material` しない |
| Direct Link の再インポートのたびに、差し替えた素材が元に戻る | 再インポートの後に `ue_material_swap.py` と `ue_attach.py` を流し直す（どちらも何度流してもよい） |
| エディタを再起動すると「Direct Link 自動再インポート」が外れ、Archicad の変更が黙って届かなくなる | 起動ごとにシーンアセットを右クリックして入れ直し、小さく動かして届くか確かめる |
| Python で動かした後にファイル → 保存しても何も書かれない | 保存の前に `ue_mark_dirty.py`。見張りは自分で動かしたアクタを「変更あり」にする |
| Python からレベルを保存・別名保存すると落ちることがある | 保存はファイルメニューから |
| 別名保存の後、見張りが古いアクタを掴んだままになる | 見張りが自動で取り直す（ログに `tick_error` → `scan`）。続く時は `ue_follow.py` を流し直す |
| 位置が数十 cm ずれたまま付いてくる | 見張りを始めた時に Unreal Engine と Archicad がずれていた。Direct Link で同期してから `ue_follow.py` を流し直す（対応を測り直す） |
| Archicad の平面図を前にしていると Direct Link は送らない | 位置は見張りが運ぶので問題ない。形や素材を変えた時は 3D ウィンドウを前にして同期する |
| Python から Direct Link シーンを再インポートすると子アクタが全部消える | 再インポートは「Direct Link 自動再インポート」（GUI）だけに任せる |
| Unreal Engine を背面にするとビューポートの再描画が止まる | 動きを見せる時は Unreal Engine を前面に置く |
| ゲームビュー（G キー）ではギズモが描かれない | マウスで動かす時は G でゲームビューを外す |
