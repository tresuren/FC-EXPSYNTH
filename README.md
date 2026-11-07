# FC-EXPSYNTH

ファミコン拡張音源カセット(VRC6/VRC7/N163)を本物のチップで鳴らす中継カートリッジ(RP2350B)。PCからUSB-MIDIで、将来はmicroSDのVGMで演奏する計画。

## 構成
- `hardware/<Rev>/` — リビジョンごとのKiCadプロジェクト(回路図・基板・フットプリント・BOM・docs・生成スクリプト)
- `firmware/` — RP2350ファーム(現在 stage1_bus_test)

## バージョン管理
- リビジョンはフォルダ(`hardware/RevE1/` など)で管理。大きな設計変更は新フォルダ(RevE2…)で行う。
- 現在: **RevE4(ドラフト)** — RevE3 の電源まわりを修正(RP2350 のコア電源インダクタ L1 をチップ横へ移動、電源配線を太く)。DRC 未接続0。詳細は `hardware/RevE4/README.md`。
- RevE3 — RevE2から microSD・USB-C を基板端へ移動(ケース用)。`hardware/RevE3/README.md`。
- RevE2 — 92x60mm、表面SMD+裏面7個手半田、配線完了。`hardware/RevE2/` に残す。
- 過去: RevE1 — 配線7本未接続のため RevE2 で置き換え。`hardware/RevE1/` に残す。
