## 点群与基函数 0.5.0

在 Windows、macOS、Linux 和 Android 上可导入 XYZ 或按化学式选择候选结构，在三维预览中确认原子位置与点群，再用 3N 方法计算振动对称性、红外偏振和拉曼张量。三语离线网页版使用相同引擎，页面首尾各留出 56 像素，表格标题和数据居中。例如 CH₄ 有 9 个振动自由度，对应 4 个基频，其中 2 个红外允许、4 个拉曼允许。输出包括选择定则和简并度。峰位和峰强还需要力常数及响应数据。

| 平台 | 下载 | 安装与启动 |
|---|---|---|
| Debian / Ubuntu 图形桌面 | [BasisCharacter-0.5.0-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Linux-all.deb) | 在下载目录执行 `sudo apt install ./BasisCharacter-0.5.0-Linux-all.deb`，从应用菜单打开「点群与基函数」或运行 `basis-character`。系统通过 xdg-utils 在默认图形浏览器中打开本地页面。 |
| Apple 芯片 Mac，macOS 12 或更新版本 | [BasisCharacter-0.5.0-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-macOS-arm64.dmg) | 打开 DMG，将 `BasisCharacter.app` 拖入「应用程序」后启动。 |
| Windows x64 | [BasisCharacter-0.5.0-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Windows-x64.zip) | 完整解压 ZIP 后打开 `BasisCharacter.exe`。若缺少 WebView2，先运行随包提供的微软离线运行时安装程序。 |
| Android 8.0 或更新版本 | [BasisCharacter-0.5.0-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Android.apk) | 在设备上打开 APK 并按系统提示安装。应用需要 Android System WebView 或 Chrome 内核 109 及以上，系统文件选择器可打开 XYZ，也可载入和保存 JSON 项目。 |

Mac 应用使用临时签名，DMG 未经 Apple 公证。Windows 主程序没有 Authenticode 发布者签名，包内的 WebView2 安装程序带有微软签名。Android APK 使用项目的独立签名密钥，后续覆盖安装须使用同一签名身份。系统可能提示无法验证桌面软件发布者。 如需直接使用浏览器，可下载三语独立 HTML。发布页还提供源码与 `SHA256SUMS.txt`。

## 點群與基函數 0.5.0

在 Windows、macOS、Linux 和 Android 上可匯入 XYZ 或依化學式選擇候選結構，在三維預覽中確認原子位置與點群，再以 3N 方法計算振動對稱性、紅外偏振和拉曼張量。三語離線網頁版使用相同引擎，頁面首尾各保留 56 像素，表格標題與資料置中。例如 CH₄ 有 9 個振動自由度，對應 4 個基頻，其中 2 個紅外允許、4 個拉曼允許。輸出包含選擇定則和簡併度。峰位和峰強還需要力常數與響應資料。

| 平台 | 下載 | 安裝與啟動 |
|---|---|---|
| Debian / Ubuntu 圖形桌面 | [BasisCharacter-0.5.0-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Linux-all.deb) | 在下載目錄執行 `sudo apt install ./BasisCharacter-0.5.0-Linux-all.deb`，從應用程式選單開啟「點群與基函數」或執行 `basis-character`。系統透過 xdg-utils 在預設圖形瀏覽器中開啟本機網頁。 |
| Apple 晶片 Mac，macOS 12 或更新版本 | [BasisCharacter-0.5.0-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-macOS-arm64.dmg) | 開啟 DMG，將 `BasisCharacter.app` 拖入「應用程式」後啟動。 |
| Windows x64 | [BasisCharacter-0.5.0-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Windows-x64.zip) | 完整解壓縮 ZIP 後開啟 `BasisCharacter.exe`。若缺少 WebView2，先執行隨附的微軟離線執行階段安裝程式。 |
| Android 8.0 或更新版本 | [BasisCharacter-0.5.0-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Android.apk) | 在裝置上開啟 APK 並依系統提示安裝。應用程式需要 Android System WebView 或 Chrome 核心 109 及以上，系統檔案選擇器可開啟 XYZ，也可載入與儲存 JSON 專案。 |

Mac 應用程式使用臨時簽章，DMG 未經 Apple 公證。Windows 主程式沒有 Authenticode 發行者簽章，內含的 WebView2 安裝程式帶有微軟簽章。Android APK 使用專案的獨立簽署金鑰，之後的覆蓋安裝須使用相同的簽署身分。系統可能提示無法驗證桌面軟體發行者。 如需直接使用瀏覽器，可下載三語獨立 HTML。發布頁另有原始碼及 `SHA256SUMS.txt`。

## Point Groups & Basis Functions 0.5.0

On Windows, macOS, Linux and Android, import XYZ coordinates or choose a candidate by molecular formula. Verify the atoms and point group in 3D, then use the 3N method to calculate vibrational symmetries, IR polarizations and Raman tensors. The three-language offline pages use the same engine. All versions centre table headers and values and leave 56 pixels of space at both page ends. For methane, 9 vibrational degrees of freedom give 4 fundamentals, with 2 IR-allowed and 4 Raman-allowed. The output reports selection rules and degeneracy. Peak positions and intensities additionally require force constants and response data.

| Platform | Download | Install and launch |
|---|---|---|
| Debian or Ubuntu desktop | [BasisCharacter-0.5.0-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Linux-all.deb) | Run `sudo apt install ./BasisCharacter-0.5.0-Linux-all.deb` in the download directory. Open Point Groups & Basis Functions from the applications menu or run `basis-character`. The launcher uses xdg-utils to open the local page in your default graphical browser. |
| Apple silicon Mac, macOS 12 or later | [BasisCharacter-0.5.0-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-macOS-arm64.dmg) | Open the DMG and drag `BasisCharacter.app` into Applications. |
| Windows x64 | [BasisCharacter-0.5.0-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Windows-x64.zip) | Extract the entire ZIP and open `BasisCharacter.exe`. If WebView2 is missing, install it using the bundled Microsoft offline runtime installer. |
| Android 8.0 or later | [BasisCharacter-0.5.0-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.5.0/BasisCharacter-0.5.0-Android.apk) | Open the APK on your device and follow the installation prompts. The app requires Android System WebView or a Chrome WebView provider version 109 or later. Use the system picker to open XYZ coordinates and to load or save JSON projects. |

The Mac app has an ad hoc signature and the DMG is unnotarized. The Windows application has no Authenticode publisher signature. Its bundled WebView2 installer is signed by Microsoft. The Android APK uses a dedicated project signing key for installation and future updates. macOS and Windows may display an unverified-publisher warning. Standalone HTML files are also available in all three languages, alongside the source archive and `SHA256SUMS.txt`.

Android APK certificate SHA-256 (io.github.lightzfpwings.basischaracter)

`CC:A2:98:BF:FF:A4:D5:91:3A:AD:4B:07:4E:3C:FD:ED:88:44:02:8F:28:EB:33:6F:08:99:DB:54:D1:A1:5E:52`
