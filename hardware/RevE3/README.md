# FC-EXPSYNTH (Rev.E3 draft) — E2 から microSD と USB-C を基板端へ移動

RevE2 の回路・部品・基板サイズ(92x60mm、表面SMD+裏面7個を手半田)はそのまま。3Dプリンタ製ケースに入れた時、microSDとUSB-Cを差し込めるよう、2個の部品の位置だけ変更した版。

## RevE2 からの変更点
- **microSDソケット(J13)を左へ 2.5mm 移動**: ソケット前面が基板左端から約1.75mm外へ出る(カードの出し入れ用)。
- **USB-Cレセプタクル(J12)を右へ 0.65mm 移動**: 前面が基板右端とそろう。
- 上記2部品の周りの配線を引き直し(約20ネット)。microSD金属シェル/GNDパッド(J13の各GNDパッド、J12のGNDパッド)は、パッドのすぐ横のビアでGND面へ接続。
- 回路・BOM・フットプリントライブラリ(部品の形状データ)は RevE2 と同じ。

## 状態(正直な現状)
- DRC(`docs/drc.rpt`、同梱の `.kicad_pro` ルール): **未接続0・クリアランス違反0・短絡0・穴間隔違反0・禁止エリア違反0**。残りは警告のみ: silk_overlap 27 / silk_over_copper 31 / silk_edge_clearance 2 / lib_footprint_issues 95 / courtyards_overlap 1(J10とJ4) / track_dangling 9 / via_dangling 1(引き直しで残った短い余り線)。
- 余り線(dangling)は、同じネットの銅箔に終端するものがあり、機械的に消すと接続が切れる場合があった。そのため残している。
- J13とJ12のGNDパッドは、パッドの上にビアがある(via-in-pad)。ハンダがビアへ流れる可能性あり。
- **電源線は 0.1mm 幅のまま**(RevE2と同じ)。電流容量・電源品質は未検証。
- **microSD(Hirose DM3AT)とUSB-C(HRO TYPE-C-31-M-12)の実物の寸法は、フットプリントからの読み取りのみ**。データシートで確認していない。ケース設計の前に要確認。
- 接触指(J10)・上部コネクタ(J11)のフットプリント寸法(仮寸法)、JLCPCB見積り、LCSC部品番号、ERC、ファーム実機動作は未確認(RevE2と同じ)。
- **画面関係(PPU)の28本はJ10/J11とも未接続のまま**。上部カセットのゲームは普通には動かない(音源のみ)。直結する試作配線は、下側の接触指付近が詰まって通らず見送った。

## 図面
- `docs/pcb_render.png`(表面)、`docs/pcb_render_back.png`(裏面、左右反転表示)、`docs/fc_sch.pdf`(回路図)、`docs/drc.rpt`(DRC結果)

## 再生成
基板は RevE2 の `FC-EXPSYNTH.kicad_pcb` から作った。`scripts/move_edge_parts_a.py`(部品移動・接触配線のはがし・GNDビア追加) → `scripts/route_fix4.py`(`HARD=1` で他の線をはがさない配線補完)/ `scripts/route_fix5.py`(クリアランスを0.103mmに緩めた版、最後の1本に使用) → 手動で重複ビアの統合とUSB-C付近の配線の位置ずらし。結果は実行ごとに変わるので、確定した配線はこのフォルダの `FC-EXPSYNTH.kicad_pcb` を正とする。
