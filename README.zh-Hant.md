# Point Group Reducer · 點群特徵標約化

[English](README.en.md) · [简体中文](README.md)

輸入表示的特徵標向量 **c**，計算重數 **a**，輸出不可約表示分解。

$$\mathbf a=\frac1h X^*W\mathbf c$$

X 每個橫列對應一個完整的複不可約表示，W 的對角元素是共軛類操作數，h 是群階。c 必須依照表中欄位順序，每類輸入一個數，不自行乘類內操作數。

## 下載與啟動

在本儲存庫的 Releases 頁面下載對應系統的 ZIP，完整解壓縮後雙擊啟動。獨立應用程式內含執行環境，無須安裝 Python 或 LaTeX。

| 系統 | 套件後綴 | 圖形介面入口 |
|---|---|---|
| Windows 64 位元 | Windows-x64.zip | PointGroupReducer/PointGroupReducer.exe |
| Mac M 系列 | macOS-arm64.zip | PointGroupReducer.app |
| Intel Mac | macOS-x64.zip | PointGroupReducer.app |

Windows 請保留程式旁的 `_internal` 資料夾；macOS 命令列入口為 `Start-CLI.command`。應用程式未經開發者簽署或 Apple 公證。私有儲存庫須登入有權限的 GitHub 帳號。

## v2.3.0 數學排版與語言切換

- 點群名稱、共軛類表頭、不可約表示與結果公式採用離線 MathText 渲染，正確顯示上下標、撇號與複共軛表示的正負號。
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

構建先執行 30 項原始碼測試，以及真實 Tk 的數學渲染、三語切換、輸入保留、複製與匯出檢查；封裝後檢查獨立 GUI/CLI 啟動與範例計算。輸出 ZIP、SHA-256 與構建紀錄。三個平台全部通過後才發佈。自動檢查不替代 Windows/macOS 實機人工點選驗收；狀態以 Actions 與 BUILD-INFO.json 為準。
