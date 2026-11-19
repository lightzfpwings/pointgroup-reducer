## 点群与基函数 0.4.6

0.4.6 将 0.4.5 的 SALC 计算封装到 Linux、macOS、Windows 和 Android。四种封装共用离线引擎，支持 87 个空间点群、423 张手动约化表和三语切换。0.5.0 的振动光谱设计在独立开发线上继续。

| 平台 | 下载 | 安装与启动 |
|---|---|---|
| Debian / Ubuntu 图形桌面 | [BasisCharacter-0.4.6-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Linux-all.deb) | 在下载目录执行 `sudo apt install ./BasisCharacter-0.4.6-Linux-all.deb`，从应用菜单打开「点群与基函数」或运行 `basis-character`。系统通过 xdg-utils 在默认图形浏览器中打开本地页面。 |
| Apple 芯片 Mac，macOS 12 或更新版本 | [BasisCharacter-0.4.6-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-macOS-arm64.dmg) | 打开 DMG，将 `BasisCharacter.app` 拖入「应用程序」后启动。 |
| Windows x64 | [BasisCharacter-0.4.6-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Windows-x64.zip) | 完整解压 ZIP 后打开 `BasisCharacter.exe`。若缺少 WebView2，先运行随包提供的微软离线运行时安装程序。 |
| Android 8.0 或更新版本 | [BasisCharacter-0.4.6-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Android.apk) | 在设备上打开 APK 并按系统提示安装。应用需要 Android System WebView 或 Chrome 内核 109 及以上，可通过系统文件选择器保存和载入 JSON。 |

Mac 应用使用临时签名，DMG 未经 Apple 公证。Windows 主程序没有 Authenticode 发布者签名，包内的 WebView2 安装程序带有微软签名。Android APK 使用项目的独立签名密钥，后续覆盖安装须使用同一签名身份。系统可能提示无法验证桌面软件发布者。 如需直接使用浏览器，可下载三语独立 HTML。发布页还提供源码与 `SHA256SUMS.txt`。

## 點群與基函數 0.4.6

0.4.6 將 0.4.5 的 SALC 計算封裝到 Linux、macOS、Windows 和 Android。四種封裝共用離線引擎，支援 87 個空間點群、423 張手動約化表及三語切換。0.5.0 的振動光譜設計在獨立開發線上繼續。

| 平台 | 下載 | 安裝與啟動 |
|---|---|---|
| Debian / Ubuntu 圖形桌面 | [BasisCharacter-0.4.6-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Linux-all.deb) | 在下載目錄執行 `sudo apt install ./BasisCharacter-0.4.6-Linux-all.deb`，從應用程式選單開啟「點群與基函數」或執行 `basis-character`。系統透過 xdg-utils 在預設圖形瀏覽器中開啟本機網頁。 |
| Apple 晶片 Mac，macOS 12 或更新版本 | [BasisCharacter-0.4.6-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-macOS-arm64.dmg) | 開啟 DMG，將 `BasisCharacter.app` 拖入「應用程式」後啟動。 |
| Windows x64 | [BasisCharacter-0.4.6-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Windows-x64.zip) | 完整解壓縮 ZIP 後開啟 `BasisCharacter.exe`。若缺少 WebView2，先執行隨附的微軟離線執行階段安裝程式。 |
| Android 8.0 或更新版本 | [BasisCharacter-0.4.6-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Android.apk) | 在裝置上開啟 APK 並依系統提示安裝。應用程式需要 Android System WebView 或 Chrome 核心 109 及以上，可透過系統檔案選擇器儲存與載入 JSON。 |

Mac 應用程式使用臨時簽章，DMG 未經 Apple 公證。Windows 主程式沒有 Authenticode 發行者簽章，內含的 WebView2 安裝程式帶有微軟簽章。Android APK 使用專案的獨立簽署金鑰，之後的覆蓋安裝須使用相同的簽署身分。系統可能提示無法驗證桌面軟體發行者。 如需直接使用瀏覽器，可下載三語獨立 HTML。發布頁另有原始碼及 `SHA256SUMS.txt`。

## Point Groups & Basis Functions 0.4.6

Version 0.4.6 packages the SALC calculations from 0.4.5 for Linux, macOS, Windows and Android. All four packages use the same offline engine, support 87 spatial groups and 423 manual reduction tables, and offer three interface languages. Vibrational spectroscopy is in development for 0.5.0.

| Platform | Download | Install and launch |
|---|---|---|
| Debian or Ubuntu desktop | [BasisCharacter-0.4.6-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Linux-all.deb) | Run `sudo apt install ./BasisCharacter-0.4.6-Linux-all.deb` in the download directory. Open Point Groups & Basis Functions from the applications menu or run `basis-character`. The launcher uses xdg-utils to open the local page in your default graphical browser. |
| Apple silicon Mac, macOS 12 or later | [BasisCharacter-0.4.6-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-macOS-arm64.dmg) | Open the DMG and drag `BasisCharacter.app` into Applications. |
| Windows x64 | [BasisCharacter-0.4.6-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Windows-x64.zip) | Extract the entire ZIP and open `BasisCharacter.exe`. If WebView2 is missing, install it using the bundled Microsoft offline runtime installer. |
| Android 8.0 or later | [BasisCharacter-0.4.6-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.4.6/BasisCharacter-0.4.6-Android.apk) | Open the APK on your device and follow the installation prompts. The app requires Android System WebView or a Chrome WebView provider version 109 or later. Use the system file picker to save and load JSON. |

The Mac app has an ad hoc signature and the DMG is unnotarized. The Windows application has no Authenticode publisher signature. Its bundled WebView2 installer is signed by Microsoft. The Android APK uses a dedicated project signing key for installation and future updates. macOS and Windows may display an unverified-publisher warning. Standalone HTML files are also available in all three languages, alongside the source archive and `SHA256SUMS.txt`.

Android APK certificate SHA-256 (io.github.lightzfpwings.basischaracter)

`CC:A2:98:BF:FF:A4:D5:91:3A:AD:4B:07:4E:3C:FD:ED:88:44:02:8F:28:EB:33:6F:08:99:DB:54:D1:A1:5E:52`
