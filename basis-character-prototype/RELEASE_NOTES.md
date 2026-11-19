## 点群与基函数 0.4.4

精简了 macOS 和 Windows 的原生界面代码，共用计算自检，并保留原来的功能、快捷键及约化器过渡动画。三语界面和离线使用均受支持。

| 平台 | 完整包 | 轻量包 |
|---|---|---|
| Windows x64 | 包含 .NET、微软签名的离线 WebView2 安装器和三份按语言预设的 HTML | 包含 .NET 和一份可切换三语的 HTML，缺少 WebView2 时可按随包链接获取 |
| macOS Apple 芯片 | 包含三份按语言预设的离线 HTML | 包含一份可切换三语的离线 HTML |

完整解压后打开 `BasisCharacter.exe` 或 `BasisCharacter.app`。发布附件另有独立网页、源码和 SHA-256 校验文件。

## Point Groups & Basis Functions 0.4.4

The native macOS and Windows code shares calculation checks and has less duplicated menu, resource and file-handling logic. Features, shortcuts and the original reducer's transitions are preserved. Full and lightweight archives contain the same app binary for each platform. The full Windows archive includes Microsoft's signed offline WebView2 installer. The lightweight Windows archive includes .NET and a link for computers that need WebView2. Both macOS archives target Apple silicon and use the system WebKit.
