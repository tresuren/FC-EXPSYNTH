# FC-EXPSYNTH (Rev.E5 draft) — 92x80mm、PPU直結・ゲームモード・データバス双方向

RevE4 を作り直した版。基板を 20mm 高くして、上に刺したカセットのゲームが動くように画面系(PPU)の線を通し、ゲーム中の音源書き込みを RP2350 が読めるようにした。部品は全部表面(JLCPCB の片面実装で全部載る。手半田は J11 など差し込み・直付けの部品だけ)。

## RevE4 からの変更点

### 回路(`FC-EXPSYNTH.kicad_sch`、`scripts/gen_sch.py`)
- **PPU バス 27 本(J10/J11 の 17〜29、47〜60 番)と /IRQ(15 番)を J10(接触指)⇔ J11(上部スロット)で直結**。ネット名 `PPU_*`、`CIRAM_*`、`IRQ_N`。
- **ゲーム/演奏モード切替**: `GAME` = GPIO30(R51 1k 経由)、R52 10k で +3V3 にプルアップ(**既定=ゲームモード**)。
  - RW_SYN = R/W AND NOT GAME(U14 の空きゲート + U15 の空きインバータ)
  - ROMSEL_EXP(J11 44番) = ROMSEL_N OR RW_SYN → ゲームモードでは上のカセットに /ROMSEL がそのまま届く。演奏モード(GPIO30 = Low)では書き込みだけ届く(RevE4 と同じ動作)。
- **データバス双方向化**: U13 を 74AHCT245(5V)→ **74LVC245(3.3V、B 側は 5V 入力対応)** に変更、DIR = R/W(読み出し: RP2350→ファミコン、書き込み: ファミコン→RP2350)。
  - **U17(74LVC1G02、新規)**: OE_N = NOT(RW_N OR OE1)。CPU の書き込みサイクルは常に U13 が開き、RP2350 がデータを読める(ゲーム中の音源レジスタ書き込みの記録用)。$8000 以上の読み出しは従来どおり EN_N で RP2350 が応答。
  - RP2350 に 5V が入らない構成(U13 の A 側は 3.3V 出力)。ファミコン側への出力は 3.3V(TTL の High 2.0V 以上)。
  - **ファーム側の注意**: CPU の書き込みサイクル中は ED0〜7(GPIO19〜26)を入力にしておくこと(U13 が RP2350 側へ出力するため。330Ω で保護はある)。
- テストパッド: TP7 = GAME、TP8 = IRQ_N(RevE4 の D0/A0 から変更)。
- 部品追加: U17、C42(U17 のパスコン)、R51、R52。部品数 99。

### 基板(`FC-EXPSYNTH.kicad_pcb`)
- **92x60mm → 92x80mm**(本体 0〜69.3mm、接触指 69.3〜80mm)。バッファ IC の列を y=52mm に置き、接触指までの配線帯を約 4mm → 約 14mm に拡大。
- **PPU の 27 本は裏面にまっすぐな縦の線(0.15mm、ロック)**: 接触指の上と J11 の下でビアを使い、裏面で 2 本 1 組(各ピンの ±0.6mm)で通す(`scripts/ppu_lanes.py`)。PPU_D4(60番)だけ USB-C の固定端子を避けて少し迂回。
- **裏面の部品なし**(RevE4 の裏 7 個のコンデンサは表面の 0402 に)。
- **水晶 Y1 を RP2350 の XIN/XOUT(30/31 番ピン)の約 4mm 下**へ。L1(コア電源インダクタ)は RevE4 と同じくピン 63 の隣。
- 電源ネット(+5V、+3V3、+1V1、VSYS、VBUS)に Power ネットクラス 0.25mm を設定して配線し、空きのある区間を最大 0.5mm に拡幅(`scripts/widen.py`)。
  - +5V: 0.5mm 57mm / 0.4mm 47mm / 0.3mm 62mm / 0.25mm 91mm(**全区間 0.25mm 以上**)
  - +3V3: 内層 In2 の面 + 配線(0.22mm 2mm 以外は 0.25mm 以上)
  - +1V1: 0.25〜0.5mm、VREG_LX 約 2mm
- 基板の縁から 0.45mm は配線・ビア禁止(自動配線が縁の規則を守らないため)。
- 部品名の文字 0.8mm / 線幅 0.12mm。

## 状態(正直な現状)
- DRC(`docs/drc.rpt`): **未接続 0・クリアランス違反 0・短絡 0・穴間隔違反 0・禁止エリア違反 0・基板端違反 0・余り線 0**。残りは警告: silk_over_copper 36 / silk_overlap 27 / lib_footprint_issues 99 / courtyards_overlap 1(J10 と J4、以前から)。
- **水晶の配線長: XIN 約 11mm、XOUT 約 13mm、C4 側 約 17mm**(Y1 自体はピンの直下だが、自動配線が C4 と R2 を少し離れた場所に置いた)。下は全面 GND 層。RevE4(約 23mm)より短いが、理想(数 mm)ではない。水晶まわりを固定して配線する案も 3 回試したが、RP2350 下側が詰まって 2〜7 本つながらなかったため、この版を採用。発振は実機で確認が必要。
- **ERC(回路図のルール検査)は未実施**(この環境の KiCad 7 の CLI に ERC がないため)。KiCad で開いて確認してほしい。
- 74LVC245 を 3.3V で使い、ファミコンのバスへ 3.3V で出す設計。ファミコン実機での読み出しタイミング・電圧の余裕は実機で確認が必要。
- J11(上部スロット)のフットプリントは仮寸法のまま(実物の 2x30 コネクタで要確認)。microSD、USB-C の実物寸法も未確認。
- LCSC 部品番号、JLCPCB 見積り、ファーム(モード切替・書き込み記録)は未着手。
- 上のカセットでゲームを動かすには: GAME = High(既定)、EN_N = High(既定)のまま。演奏モードでは RP2350 が GPIO30 を Low にしてから、本体のリセットボタンを押す想定。

## 図面
- `docs/pcb_render.png`(表面)、`docs/pcb_render_back.png`(裏面、左右反転表示)、`docs/fc_sch.pdf`(回路図)、`docs/drc.rpt`(DRC)、`BOM.csv`(部品表、`scripts/make_bom.py` で基板から生成)

## 再生成
1. `python3 scripts/gen_sch.py` → `kicad-cli sch export netlist -o fc.net FC-EXPSYNTH.kicad_sch`
2. `scripts/build_all.sh`(部品配置 `build_pcb.py` → `.kicad_pro` の規則を戻す → `ppu_lanes.py`)
3. `FR_JAR=... scripts/run_fr.sh`(Freerouting で自動配線 → `route.ses`)→ `python3 scripts/imp.py`
4. `HARD=1 python3 scripts/route_fix6.py <dir>`(残りの補修) → `scripts/widen.py`(電源線を太く)
自動配線は実行ごとに結果が変わる。確定した配線はこのフォルダの `FC-EXPSYNTH.kicad_pcb` を正とする(+3V3 の 50 番ピンと GPIO36 は手で補修済み)。
