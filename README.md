# FC-EXPSYNTH

ファミコン拡張音源カセット(VRC6/VRC7/N163)を本物のチップで鳴らす中継カートリッジ(RP2350B)。PCからUSB-MIDIで、将来はmicroSDのVGMで演奏する計画。

## 構成
- `hardware/<Rev>/` — リビジョンごとのKiCadプロジェクト(回路図・基板・フットプリント・BOM・docs・生成スクリプト)
- `firmware/` — RP2350ファーム(現在 stage1_bus_test)

## バージョン管理
- リビジョンはフォルダ(`hardware/RevE1/` など)で管理。大きな設計変更は新フォルダ(RevE2…)で行う。
- 現在: **RevE5(ドラフト)** — 92x80mm、PPU バスと /IRQ を上部スロットへ直結(上のカセットのゲームが動く想定)、ゲーム/演奏モード切替、データバス双方向(ゲーム中の音源書き込みを記録用に読める)、全部品表面実装。DRC 未接続0。詳細は `hardware/RevE5/README.md`。
- RevE4 — RevE3 の電源まわりを修正(L1 をチップ横へ、電源配線を太く)。`hardware/RevE4/README.md`。
- RevE3 — RevE2から microSD・USB-C を基板端へ移動(ケース用)。`hardware/RevE3/README.md`。
- RevE2 — 92x60mm、表面SMD+裏面7個手半田、配線完了。`hardware/RevE2/` に残す。
- 過去: RevE1 — 配線7本未接続のため RevE2 で置き換え。`hardware/RevE1/` に残す。
