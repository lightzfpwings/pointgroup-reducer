## 点群与基函数 0.7.0

0.7.0 在版本号旁增加「检查更新」。点击后查询 GitHub 的本软件正式版，发现新版可在界面内选择「安装更新」。请先保存当前项目。分子结构查询、振动和红外／拉曼计算均可离线使用。

0.6.0 及更早版本需要先从发布页安装一次 0.7.0。Android 校验包名、签名和版本，再交由系统覆盖安装，首次可能需要允许此应用安装更新。Windows 在原解压目录更新并重启，macOS 替换应用包并重新启动。Debian／Ubuntu 使用系统授权安装新版 DEB。独立 HTML 可在支持文件写入的浏览器中选择原文件覆盖，其他浏览器可下载同语言 HTML 后替换。安装包在替换前按发布附件的 SHA-256 校验。

| 平台 | 下载 | 安装与启动 |
|---|---|---|
| Debian / Ubuntu 图形桌面 | [BasisCharacter-0.7.0-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Linux-all.deb) | 在下载目录执行 `sudo apt install ./BasisCharacter-0.7.0-Linux-all.deb`，从应用菜单打开「点群与基函数」或运行 `basis-character`。系统通过 xdg-utils 在默认图形浏览器中打开本地页面。 |
| Apple 芯片 Mac，macOS 12 或更新版本 | [BasisCharacter-0.7.0-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-macOS-arm64.dmg) | 打开 DMG，将 `BasisCharacter.app` 拖入「应用程序」后启动。 |
| Windows x64 | [BasisCharacter-0.7.0-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Windows-x64.zip) | 完整解压 ZIP 后打开 `BasisCharacter.exe`。若缺少 WebView2，先运行随包提供的微软离线运行时安装程序。 |
| Android 8.0 或更新版本 | [BasisCharacter-0.7.0-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Android.apk) | 在设备上打开 APK 并按系统提示安装。应用需要 Android System WebView 或 Chrome 内核 109 及以上，系统文件选择器可打开 XYZ，也可载入和保存 JSON 项目。 |

Mac 应用使用临时签名，DMG 未经 Apple 公证。Windows 主程序没有 Authenticode 发布者签名，包内的 WebView2 安装程序带有微软签名。Android APK 使用项目的独立签名密钥，后续覆盖安装须使用同一签名身份。系统可能提示无法验证桌面软件发布者。 如需直接使用浏览器，可下载三语独立 HTML。发布页还提供源码与 `SHA256SUMS.txt`。

## 點群與基函數 0.7.0

0.7.0 在版本號旁新增「檢查更新」。點選後查詢 GitHub 的本軟體正式版，發現新版可在介面選擇「安裝更新」。請先儲存目前的專案。分子結構查詢、振動和紅外／拉曼計算均可離線使用。

0.6.0 及更早版本必須先從發布頁安裝一次 0.7.0。Android 核對套件名稱、簽章和版本，再交由系統覆蓋安裝，首次可能需要允許此應用程式安裝更新。Windows 在原解壓縮目錄更新並重新啟動，macOS 替換應用程式套件並重新啟動。Debian／Ubuntu 使用系統授權安裝新版 DEB。獨立 HTML 可在支援檔案寫入的瀏覽器選擇原檔案覆蓋，其他瀏覽器可下載同語言 HTML 後替換。安裝套件在替換前依發布附件的 SHA-256 驗證。

| 平台 | 下載 | 安裝與啟動 |
|---|---|---|
| Debian / Ubuntu 圖形桌面 | [BasisCharacter-0.7.0-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Linux-all.deb) | 在下載目錄執行 `sudo apt install ./BasisCharacter-0.7.0-Linux-all.deb`，從應用程式選單開啟「點群與基函數」或執行 `basis-character`。系統透過 xdg-utils 在預設圖形瀏覽器中開啟本機網頁。 |
| Apple 晶片 Mac，macOS 12 或更新版本 | [BasisCharacter-0.7.0-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-macOS-arm64.dmg) | 開啟 DMG，將 `BasisCharacter.app` 拖入「應用程式」後啟動。 |
| Windows x64 | [BasisCharacter-0.7.0-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Windows-x64.zip) | 完整解壓縮 ZIP 後開啟 `BasisCharacter.exe`。若缺少 WebView2，先執行隨附的微軟離線執行階段安裝程式。 |
| Android 8.0 或更新版本 | [BasisCharacter-0.7.0-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Android.apk) | 在裝置上開啟 APK 並依系統提示安裝。應用程式需要 Android System WebView 或 Chrome 核心 109 及以上，系統檔案選擇器可開啟 XYZ，也可載入與儲存 JSON 專案。 |

Mac 應用程式使用臨時簽章，DMG 未經 Apple 公證。Windows 主程式沒有 Authenticode 發行者簽章，內含的 WebView2 安裝程式帶有微軟簽章。Android APK 使用專案的獨立簽署金鑰，之後的覆蓋安裝須使用相同的簽署身分。系統可能提示無法驗證桌面軟體發行者。 如需直接使用瀏覽器，可下載三語獨立 HTML。發布頁另有原始碼及 `SHA256SUMS.txt`。

## Point Groups & Basis Functions 0.7.0

Version 0.7.0 adds Check for updates next to the version number. Check GitHub for a stable release of this app, save your project and select Install update. Molecular lookup, vibrations and IR/Raman calculations work offline.

Users of 0.6.0 or earlier need to install 0.7.0 once from this release. Android checks package identity, signing certificate and version before opening the system installer. Allow this app to install updates when Android asks. Windows updates the extracted application in place and restarts. macOS replaces and reopens the app. Debian/Ubuntu requests system authorization to install the new DEB. For standalone HTML, select the original file in a browser with file-write support, or download the HTML in your language and replace it manually. Installers verify the release asset’s SHA-256 before replacement.

| Platform | Download | Install and launch |
|---|---|---|
| Debian or Ubuntu desktop | [BasisCharacter-0.7.0-Linux-all.deb](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Linux-all.deb) | Run `sudo apt install ./BasisCharacter-0.7.0-Linux-all.deb` in the download directory. Open Point Groups & Basis Functions from the applications menu or run `basis-character`. The launcher uses xdg-utils to open the local page in your default graphical browser. |
| Apple silicon Mac, macOS 12 or later | [BasisCharacter-0.7.0-macOS-arm64.dmg](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-macOS-arm64.dmg) | Open the DMG and drag `BasisCharacter.app` into Applications. |
| Windows x64 | [BasisCharacter-0.7.0-Windows-x64.zip](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Windows-x64.zip) | Extract the entire ZIP and open `BasisCharacter.exe`. If WebView2 is missing, install it using the bundled Microsoft offline runtime installer. |
| Android 8.0 or later | [BasisCharacter-0.7.0-Android.apk](https://github.com/lightzfpwings/pointgroup-reducer/releases/download/basis-v0.7.0/BasisCharacter-0.7.0-Android.apk) | Open the APK on your device and follow the installation prompts. The app requires Android System WebView or a Chrome WebView provider version 109 or later. Use the system picker to open XYZ coordinates and to load or save JSON projects. |

The Mac app has an ad hoc signature and the DMG is unnotarized. The Windows application has no Authenticode publisher signature. Its bundled WebView2 installer is signed by Microsoft. The Android APK uses a dedicated project signing key for installation and future updates. macOS and Windows may display an unverified-publisher warning. Standalone HTML files are also available in all three languages, alongside the source archive and `SHA256SUMS.txt`.

Android APK certificate SHA-256 (io.github.lightzfpwings.basischaracter)

`CC:A2:98:BF:FF:A4:D5:91:3A:AD:4B:07:4E:3C:FD:ED:88:44:02:8F:28:EB:33:6F:08:99:DB:54:D1:A1:5E:52`
