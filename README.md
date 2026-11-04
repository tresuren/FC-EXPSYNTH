# FC-EXPSYNTH

ファミコン拡張音源カセット(VRC6/VRC7/N163)を本物のチップで鳴らす中継カートリッジ(RP2350B)。PCからUSB-MIDIで、将来はmicroSDのVGMで演奏する計画。

## 構成
- `hardware/<Rev>/` — リビジョンごとのKiCadプロジェクト(回路図・基板・フットプリント・BOM・docs・生成スクリプト)
- `firmware/` — RP2350ファーム(現在 stage1_bus_test)

## バージョン管理
- リビジョンはフォルダ(`hardware/RevE1/` など)で管理。大きな設計変更は新フォルダ(RevE2…)で行う。
- 現在: **RevE1(ドラフト)** — 92x60mm・片面SMD、配線は一部未接続。詳細は `hardware/RevE1/README.md`。
