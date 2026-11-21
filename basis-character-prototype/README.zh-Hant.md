# 點群與基函數 0.7.0

在本目錄執行 `python3 build.py`，開啟 [0.7.0 繁體中文離線版](dist/BasisCharacterPrototype-0.7.0-zh-Hant.html)。選擇「振動光譜（紅外與拉曼）」，開啟[水分子 XYZ](examples/water.xyz)，在三維預覽下方選擇 C₂ᵥ，點選「確認結構與點群」，再點選「計算振動與光譜活性」。

手邊只有化學式時，可在同一入口輸入 `C2H6O`，點選「尋找候選結構」，再選「乙醇 · 反式構形」或「二甲醚」。下方會顯示所選模型的三維結構、原子座標與點群。確認後即可比較兩種結構的紅外與拉曼活性。

[简体中文](README.md) · [English](README.en.md)

可從 s/p/d 基函數及分子幾何建立表示矩陣、約化特徵標，再產生各不可約副本的 SALC 係數。亦可直接輸入特徵標進行約化。

0.6.0 新增 39 個常見有機物模型及 21 個配合物模型。離線庫現有 221 個候選結構，涵蓋 196 種依電荷區分的化學式。

0.7.0 在版本號旁新增「檢查更新」。點選後查詢 GitHub 的本軟體正式版，發現新版可在介面選擇「安裝更新」。請先儲存目前的專案。分子結構查詢、振動和紅外／拉曼計算均可離線使用。

0.6.0 及更早版本必須先從發布頁安裝一次 0.7.0。Android 核對套件名稱、簽章和版本，再交由系統覆蓋安裝，首次可能需要允許此應用程式安裝更新。Windows 在原解壓縮目錄更新並重新啟動，macOS 替換應用程式套件並重新啟動。Debian／Ubuntu 使用系統授權安裝新版 DEB。獨立 HTML 可在支援檔案寫入的瀏覽器選擇原檔案覆蓋，其他瀏覽器可下載同語言 HTML 後替換。安裝套件在替換前依發布附件的 SHA-256 驗證。

## 下載與安裝

| 平台 | 下載 | 安裝與啟動 |
|---|---|---|
| Debian / Ubuntu 圖形桌面 | [BasisCharacter-0.7.0-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Linux-all.deb) | 在下載目錄執行 `sudo apt install ./BasisCharacter-0.7.0-Linux-all.deb`，從應用程式選單開啟「點群與基函數」或執行 `basis-character`。系統透過 xdg-utils 在預設圖形瀏覽器中開啟本機網頁。 |
| Apple 晶片 Mac，macOS 12 或更新版本 | [BasisCharacter-0.7.0-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-macOS-arm64.dmg) | 開啟 DMG，將 `BasisCharacter.app` 拖入「應用程式」後啟動。 |
| Windows x64 | [BasisCharacter-0.7.0-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Windows-x64.zip) | 完整解壓縮 ZIP 後開啟 `BasisCharacter.exe`。若缺少 WebView2，先執行隨附的微軟離線執行階段安裝程式。 |
| Android 8.0 或更新版本 | [BasisCharacter-0.7.0-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Android.apk) | 在裝置上開啟 APK 並依系統提示安裝。應用程式需要 Android System WebView 或 Chrome 核心 109 及以上，系統檔案選擇器可開啟 XYZ，也可載入與儲存 JSON 專案。 |

Mac 應用程式使用臨時簽章，DMG 未經 Apple 公證。Windows 主程式沒有 Authenticode 發行者簽章，內含的 WebView2 安裝程式帶有微軟簽章。Android APK 使用專案的獨立簽署金鑰，之後的覆蓋安裝須使用相同的簽署身分。系統可能提示無法驗證桌面軟體發行者。 [簽章說明](SIGNING.md)

如需直接使用瀏覽器，可下載三語獨立 HTML。發布頁另有原始碼及 `SHA256SUMS.txt`。 [下載 0.7.0](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.7.0)

「由基函數計算」支援 87 個已驗證的空間點群，從代表座標展開位置，或逐中心輸入。添加 s、p、五個實 d 分量後，自動建立表示矩陣、識別封閉計算塊、計算特徵標，再約化全體及各塊。

「手動輸入特徵標」保留原程式可選的 423 個有限點群。依表格欄位順序，每個共軛類輸入一個數，不乘類大小；可用逗號或分號分隔，並支援 i、π、sqrt、cos、sin、exp 和算術運算式。完整複不可約表示中的共軛行分別保留。公式為 `a = X.conj() @ W @ c / h`，重數須為非負整數，且能在容差內重建輸入；非法輸入不會顯示成功分解。

兩種方式共用共軛類約定、MathML 數學排版、文字及 LaTeX 複製、輸入儲存與完整結果匯出。0.1–0.3 版基函數 JSON 仍可開啟；開啟後重新計算，不沿用舊結果。

以「由基函數計算」完成分解後，點選「產生 SALC 係數」，依不可約表示和副本檢視。每一欄給出一個組合 $\psi = \sum_j c_j \phi_j$，各列依原輸入函數排列。複製包含當前副本，完整 JSON 匯出包含所有已產生的副本。水範例以 xz 為分子平面，兩個 H 1s 函數分別給出 A1 的正規化和與 B1 的正規化差，係數絕對值均為 1/√2。

特徵標投影算符為 $P_\alpha = \frac{d_\alpha}{|G|}\sum_{g\in G}\chi_\alpha(g)^*D(g)$，星號表示複共軛。對於重複出現的多維表示，程式逐副本建立夥伴函數，檢查正交性、在生成元下的封閉性及特徵標。不同中心、徑向識別碼或角動量之間視為正交，同組 p 使用方向內積，d 使用張量 Frobenius 內積。整體相位、簡併空間內的基與等價副本的選取具有自由度。[MIT 群表示講義](https://ocw.mit.edu/courses/18-712-introduction-to-representation-theory-fall-2010/24d8b3fa2ce48e48ee6c2d8d5e3562f6_MIT18_712F10_replect.pdf)

可先試「中心 d · Oₕ」：五個全域 d 分量自動形成 3+2 維封閉塊，分解為 T2g + Eg。C2v 的五個 d 分量各自封閉，總體為 2A1 + A2 + B1 + B2。水範例的兩個 H s 為 A1 + B1。苯的 30 個函數形成四個封閉塊，各獨立等價副本均保留。

d 採五維實球諧函數 dxy、dxz、dyz、dx²−y²、dz²；dz² 指 2z²−x²−y²。張量 Q 對稱且無跡，按 Frobenius 內積正交正規化，主動變換為 `Q → RQRᵀ`。局部軸矩陣的欄為 x′/y′/z′ 在全域座標中的方向。進階設定輸入垂直的 x′、z′，系統建立右手 y′；中心不限於原點，但須符合所選對稱性。不同中心可分別選取新增不同局部軸。

對非正交角向基採用 QR 分解展開，並檢查每次變換的重建殘差。

目前最多 120 個中心、180 個函數。徑向 ID 是副本識別碼，尚無量子化學基組庫。封閉計算塊不等於不可約表示；換基可能改變塊結構。尚未實作六維 Cartesian d、自動點群辨識、AO 重疊積分或電子能量。

顯示表格的根式與公式，實際計算採雙精度；匯出保留完整數值和容差，不將數值結果視為符號證明。原有 Python 約化程式保持相容，整合版位於獨立目錄；同步 sources 未修改，執行整合版不依賴原 Python 程式。測試逐項核對原程式的 423 張完整複表與各不可約行，並檢查整合流程、運算式、三語狀態與舊檔相容性。

0.4.2 修正軌道與方向下標、群名及不可約符號上下標、角度分數、科學記號，以及直立的虛數單位與函數名稱。粗體 a/X/W/c 的星號明確表示逐項複共軛，不含轉置。MathML 與 LaTeX 共用運算式樹，保留負號、分數、冪及括號的數值含義；小的非零數不再顯示為零。

0.4.2 修復數學表頭顯示為 `[object MathMLMathElement]` 的問題。表頭與正文共用節點插入邏輯；三語特徵標表、基函數結果表、手動結果表及向量表均檢查數學表頭節點。

0.4.3 新增 Windows x64 原生封裝、系統 JSON 對話框、剪貼簿與三語選單，並修復位置容差編輯。在 Windows x64 安裝 .NET 10 SDK 後執行 `python packaging/build_windows.py` 即可封裝。封裝自檢以 Jint 執行與 Mac 共用的計算指令碼。0.4.4 的 Windows 應用程式未使用 Authenticode 簽章。原始發布版附 WebView2 離線安裝程式，輕量包提供微軟下載捷徑。

## 0.5.0 振動光譜

「振動光譜（紅外與拉曼）」使用所選空間點群和分子中所有原子的座標，包括位於對稱中心的原子。可開啟或貼上單幀 XYZ、手動輸入座標或載入專案。XYZ 首列填寫原子數（1–120），第二列為註解或空列，之後每列填寫元素與三個以 Å 為單位的座標。D 與 T 可作為相異的同位素類型。

在振動光譜的「結構目錄」可依名稱瀏覽有機物與配合物，也可輸入化學式。輸入 `C4H8` 可比較順式與反式 2-丁烯、異丁烯及環丁烷。輸入 `Pt(NH3)2Cl2` 可比較順鉑與反鉑。輸入 `[Fe(CN)6]4-` 可指定亞鐵氰根，省略電荷則同時列出鐵(II)與鐵(III)候選。每次選擇後，先核對三維結構並確認，再計算紅外與拉曼選擇定則。全部座標隨應用程式提供，Android 可離線使用。

新增有機物中，17 個模型採用 NIST CCCBDB 參考座標，經重新定向與對稱化以處理座標捨入誤差。α/β-D-吡喃葡萄糖與 D/L-丙胺酸採用 PubChem 計算構象。其餘新增模型採用理想化幾何，配合物明確包含配體上的原子。二茂鐵提供重疊式與交錯式兩種環取向。原有碳、矽四面體取代模型仍可依化學式查詢。專案 JSON 儲存所選候選、電荷（如有）與用於計算的完整座標。 [NIST CCCBDB](https://cccbdb.nist.gov/exp2x.asp?casno=74840&charge=0) · [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/79025)

旋轉模型，對照原子編號與座標表。選擇 A、B、C 可量測 A–B 距離及以 B 為頂點的夾角。XYZ 預覽中的灰色連線依共價半徑估算，綠線連接選取量測的原子。確認時程式檢查所有同類型原子在所選點群下的一一映射，並顯示最大位置偏差。XYZ 預設以幾何中心為對稱原點，保留檔案的軸向與原始座標。請核對點群的軸向提示，需要時可先在分子編輯器對齊座標再匯入。變更結構、點群、原點或容差後須再次確認。[XYZ 格式](https://openbabel.org/docs/FileFormats/XYZ_cartesian_coordinates_format.html) · [共價半徑資料](https://doi.org/10.1039/B801115J)

確認後點選「計算振動與光譜活性」。各操作的笛卡兒位移特徵標等於固定原子數乘以空間矩陣的跡。扣除整體平移及轉動後，非線性分子有 3N−6 個振動自由度，線性分子有 3N−5 個，單原子為 0。紅外允許的振動與偶極向量同對稱性，拉曼允許的振動與對稱極化率張量的六個分量之一同對稱性。

簡併分量合計為一個基頻，複共軛行亦成對計數。使用有限子群時，簡併度和計數均依該子群決定。峰位需要質量與力常數，強度還需要偶極矩或極化率對簡正座標的導數。可直接載入甲烷 Td 或二氧化碳 D4h 振動範例。甲烷的 9 個振動自由度分解為 A1 + E + 2T2，對應 4 個基頻，其中 2 個紅外允許、4 個拉曼允許。基頻對稱性與 NIST 的實驗歸屬一致。[NIST 甲烷振動資料](https://cccbdb.nist.gov/exp2x.asp?casno=74828)

以 xz 平面內的水為例，兩個 A₁ 振動均允許 z 偏振，且各有三個獨立的拉曼張量分量 xx、yy、zz。B₁ 振動允許 x 偏振和 xz 分量。對沿 z 軸的 CO₂，A₁g 列中的「xx + yy, zz」表示 xx 與 yy 相等，zz 可獨立變化。xy、xz、yz 各代表一對相等的非對角元素。複製結果會保留這些組合，JSON 的 `spectrum.activities` 儲存每列的單位偶極方向 `irDirections` 及按 Frobenius 範數歸一化的對稱矩陣 `ramanTensors`。[計算方法與驗收範例](SPECTROSCOPY_DESIGN.md)
