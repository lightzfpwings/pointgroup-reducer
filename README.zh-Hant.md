# Point Group Reducer · 點群特徵標約化

[English](README.en.md) · [简体中文](README.md)

## 點群與基函數整合版 0.4.3

[下載整合版](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.4.3) · [完整說明](basis-character-prototype/README.zh-Hant.md)

新增完整流程：位置與 s/p/d 基函數 → 可約特徵標 → 全體與各封閉塊的不可約組成。幾何入口支援 87 個真實空間點群，手動約化入口支援 423 個點群。介面、公式、上下標及 LaTeX 輸出統一，繁體中文／简体中文／English 可切換並保留輸入與結果。

Windows x64 下載 `BasisCharacter-0.4.3-Windows-x64.zip`，完整解壓縮後開啟 `BasisCharacter.exe`；若有提示，先執行隨包的微軟離線 WebView2 安裝器。Apple 晶片 Mac 下載 `BasisCharacter-0.4.3-macOS-arm64.zip` 並開啟 `BasisCharacter.app`。兩版共用三語介面，另提供離線 HTML。

整合版位於 `basis-character-prototype/`，使用獨立版本標籤 `basis-v0.4.3`。原 Python/Tk 約化程式及 CLI 保留，原生 Windows 舊版見 [v2.4.3](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/v2.4.3)。以下為原 Python/Tk 版本說明。

輸入表示的特徵標向量 **c**，計算重數 **a**，輸出不可約表示分解。

$$\mathbf a=\frac1h X^*W\mathbf c$$

X 每個橫列對應一個完整的複不可約表示，W 的對角元素是共軛類操作數，h 是群階。c 必須依照表中欄位順序，每類輸入一個數，不自行乘類內操作數。

## 下載與啟動

在本儲存庫的 Releases 頁面下載對應系統的 ZIP，完整解壓縮後雙擊啟動。獨立應用程式內含執行環境，無須安裝 Python 或 LaTeX。

| 系統 | 套件後綴 | 圖形介面入口 |
|---|---|---|
| Windows 64 位元 | Windows-x64.zip | PointGroupReducer/PointGroupReducer.exe |
| Mac M 系列 | macOS-arm64.zip | PointGroupReducer.app |

Windows 請保留程式旁的 `_internal` 資料夾；macOS 命令列入口為 `Start-CLI.command`。應用程式未經開發者簽署或 Apple 公證。

## 數學排版與語言切換

- 點群名稱、操作表頭、特徵標、不可約表示與結果公式採用離線數學排版，顯示上下標、根號、分數、虛數 i、π 與角度。
- 表頭與列高依公式尺寸調整，符號置中；不顯示類內操作數列及左上角標題。
- 結果頁與複製文字保留分解、特徵標、重數和表示維度，不再顯示底部重建誤差。
- 右上角或「語言」選單可切換 **English / 简体中文 / 繁體中文**；按鈕、步驟提示、錯誤訊息與使用說明同步更新。
- 切換語言保留點群、c、貼上框內容與計算結果；下次啟動沿用已儲存的語言偏好。
- 結果頁可「複製文字」或「複製 LaTeX」。LaTeX 包含約化公式、c/a 向量與合法表示的分解。
- 命令列支援 `--lang en` / `--lang zh-Hans` / `--lang zh-Hant`；互動步驟中輸入 `lang` 可切換語言。
- JSON 中的點群標籤、類順序與資料欄位不隨介面語言改變。

## 操作

選擇點群 → 輸入特徵標 c → 查看結果。d 軌域範例僅填入數值，請再按「計算」。輸入不完整或有誤時，訊息會指出對應共軛類。

| 操作 | 圖形介面 | 命令列 |
|---|---|---|
| 返回上一步 | 上一步 / Esc | `0` |
| 返回首頁 | 返回首頁；Windows Ctrl+Home / Mac Command+Shift+H | `home` |
| 結束 | 結束；Windows Ctrl+Q / Mac Command+Q | `q` |
| 單獨輸入數值零 | `0` | `=0` |

返回與首頁保留輸入；更換點群清空舊輸入。逗號向量內的 `0` 可直接寫。

## 支援範圍

下拉清單提供 **423 個點群**：Cn/Cnv/Cnh 與 Dn/Dnh/Dnd 的 n=2…60、S4…S120（偶數），以及 C1、Cs、Ci 與七個多面體點群。輸入名稱可篩選清單；更高階可直接輸入名稱並按 Enter 載入。

對稱操作表頭直接顯示旋轉、鏡面或反演名稱。例如 C2v 的四欄為 E、C2、σᵥ(xz)、σᵥ(yz)。軸向點群的主旋轉軸預設沿 z（包括 C3 及更高階軸）；xy 為水平面，xz、yz 為垂直面。其他鏡面或垂直二重軸用精確方位角 φ 標註，從 +x 向 +y 測量。多面體群可選一條最高階旋轉軸為 z，同一類的其他等價軸不必平行於 z。名稱調整保留原有欄位順序及對應特徵標。

有限普通三維點群：C1、Cs、Ci；Cn、Cnv、Cnh；Dn、Dnh、Dnd；S2n；T、Th、Td、O、Oh、I、Ih。系列按需產生，目前 n ≤ 2000；大 n 的稠密矩陣需要較多記憶體。

支援複特徵標、非負整數重數檢查、d 軌域範例、JSON/CSV 匯出。E+ / E− 各為一維複共軛表示，不可各視為二維 E。標籤與類順序可能不同於教材，以程式顯示為準。無限點群 C∞v、D∞h 不適用有限矩陣公式；不包含雙群、磁群或空間群。

## 從原始碼執行

Python 3.10+，含 Tkinter。

```bash
python -m pip install -r requirements.txt
python pointgroup.py --gui --lang zh-Hant
python pointgroup.py C2v --c "5,1,1,1" --lang zh-Hant
python pointgroup.py --lang zh-Hant
python -m unittest -v
```

數值支援 `1/2`、`sqrt(5)`、`1+2i`、`exp(2*pi*i/3)` 等受限運算式。

## 封裝與驗證

在目標 Windows 或 macOS 的原生 Python 3.12 環境：

```bash
python -m pip install -r requirements-build.txt
python packaging/build_native.py
```

構建先執行 51 項原始碼測試，以及真實 Tk 的數學渲染、三語切換、輸入保留、複製與匯出檢查；封裝後檢查獨立 GUI/CLI 啟動與範例計算。輸出 ZIP、SHA-256 與構建紀錄。只構建 Windows x64 與 Apple 晶片 Mac，兩個平台通過後才發佈。main 分支的 `[release]` 提交、VERSION 對應標籤或手動選擇 publish 可觸發發佈。發佈頁提供兩個 ZIP 與統一的 SHA256SUMS.txt；狀態以 Actions 與 BUILD-INFO.json 為準。
