# FC-EXPSYNTH

ファミコン拡張音源カセット(VRC6/VRC7/N163)を本物のチップで鳴らす中継カートリッジ(RP2350B)。PCからUSB-MIDIで、将来はmicroSDのVGMで演奏する計画。

## 構成
- `hardware/<Rev>/` — リビジョンごとのKiCadプロジェクト(回路図・基板・フットプリント・BOM・docs・生成スクリプト)
- `firmware/` — RP2350ファーム(現在 stage1_bus_test)

## バージョン管理
- リビジョンはフォルダ(`hardware/RevE1/` など)で管理。大きな設計変更は新フォルダ(RevE2…)で行う。
- 現在: **RevE2(ドラフト)** — 92x60mm、表面SMD+裏面7個手半田、配線完了(DRC 未接続0)。詳細は `hardware/RevE2/README.md`。
- 過去: RevE1 — 配線7本未接続のため RevE2 で置き換え。`hardware/RevE1/` に残す。
