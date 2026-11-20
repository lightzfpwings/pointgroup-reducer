# 四平台直接分发与签名

0.5.1 提供 Linux 的 DEB、Apple 芯片 Mac 的 DMG、Windows x64 的完整 ZIP，以及 Android 的 APK。各文件的 SHA-256 列在同页的 `SHA256SUMS.txt`。[0.5.1 下载页](https://github.com/lightzfpwings/pointgroup-reducer/releases/tag/basis-v0.5.1)

本次直接分发的 Mac 应用使用临时签名，DMG 未经 Apple 公证。Windows 主程序没有 Authenticode 发布者签名，完整 ZIP 内的 WebView2 离线安装程序带有微软签名。Linux DEB 安装离线页面和桌面入口。Android APK 采用项目独立的签名身份，可直接在设备上安装。请长期保管项目的 Android 私钥和备份，后续 APK 使用同一签名身份，便于现有用户覆盖更新。

以下是维护者构建受信任发布者签名桌面包的流程。Mac 使用 Developer ID Application、强化运行时和 Apple 公证。Windows 使用受系统信任的 Authenticode 发布者签名及时间戳。SmartScreen 还会根据文件信誉显示提示。

- Mac 安装可使用 `BasisCharacter-<版本>-macOS-arm64.dmg`。打开后将应用拖入「应用程序」。选择签名与公证构建时，应用与外层 DMG 都带有 Developer ID 签名和 Apple 公证凭据。开发用 DMG 仍可能触发 Gatekeeper 提示。 [Apple 的软件封装指南](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution)
- [Apple 的下载应用提示](https://support.apple.com/102445)
- [Microsoft 的 SmartScreen 信誉说明](https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation)

## 首次在 Mac 上签名

1. 使用开启双重认证的 Apple 账户加入 Apple Developer Program。如果已有有效会员资格，可以沿用。个人可以申请，Apple 公布的会费为每年 99 美元，实际金额以注册地区显示为准。 [注册与费用](https://developer.apple.com/programs/enroll/)
2. 由团队账户持有人在 Xcode 的 Settings → Accounts → Manage Certificates 创建 **Developer ID Application** 证书。如果通过 Apple Developer 网站申请，则先在本机「钥匙串访问 → 证书助理」生成证书请求，上传后下载 `.cer`，再导入生成请求的同一台 Mac。用 `security find-identity -v -p codesigning` 确认证书和私钥已配对。 [生成证书请求](https://developer.apple.com/help/account/certificates/create-a-certificate-signing-request/) · [申请 Developer ID](https://developer.apple.com/help/account/certificates/create-developer-id-certificates/)
3. 在 Apple 账户设置生成一个 App 专用密码。找到开发者团队的 Team ID，将下列示例值换成自己的信息。命令会提示输入专用密码并将其存入钥匙串。 [Apple 公证认证说明](https://developer.apple.com/documentation/technotes/tn3147-migrating-to-the-latest-notarization-tool)

```bash
xcrun notarytool store-credentials basis-notary \
  --apple-id '你的 Apple 账户邮箱' --team-id '你的 Team ID'
```

在整合模块目录执行，签名身份可填证书指纹，也可填钥匙串显示的证书全名。

```bash
MACOS_SIGNING_IDENTITY='Developer ID Application: 证书中的姓名 (TEAMID)' \
MACOS_NOTARY_PROFILE=basis-notary \
python3 packaging/build_macos.py --with-full --with-dmg --sign-and-notarize
```

脚本会构建 ZIP 和 DMG、提交公证、附加票据并验证最终文件。Apple 公证可用于 GitHub 直接分发。完成本机签名后即可配置下方的自动发布。纯本地安装测试可运行 `python3 packaging/build_macos.py --with-dmg`，生成采用临时应用签名的包。

## 配置 GitHub 自动签名

在仓库 Settings → Environments 建立 `basis-release-signing` 环境，将可部署分支限制为 `main`。在该环境配置下表中的 Secrets 和 Variables。此前发布的 ZIP 继续对应各自的版本标签，新签名版本使用新的标签。

| 平台 | 类型 | 名称与值 |
| --- | --- | --- |
| macOS | Secret | `MACOS_CERTIFICATE_BASE64`，Developer ID Application 证书及私钥导出的 PKCS#12 文件，Base64 编码 |
| macOS | Secret | `MACOS_CERTIFICATE_PASSWORD`，上述 PKCS#12 密码 |
| macOS | Variable | `MACOS_SIGNING_IDENTITY`，Developer ID Application 证书指纹或全名 |
| macOS | Secret | `MACOS_NOTARY_KEY_BASE64`，App Store Connect 团队 API 私钥文件 `.p8` 的 Base64 编码 |
| macOS | Variable | `MACOS_NOTARY_KEY_ID`、`MACOS_NOTARY_ISSUER_ID`，API Key ID 和 Issuer ID |
| Windows | Secret | `AZURE_CLIENT_ID`、`AZURE_TENANT_ID`、`AZURE_SUBSCRIPTION_ID`，用于 Entra 联合身份登录 |
| Windows | Variable | `AZURE_SIGNING_ENDPOINT`、`AZURE_SIGNING_ACCOUNT`、`AZURE_SIGNING_PROFILE`，Artifact Signing Public Trust 配置 |
| Windows | Variable | `WINDOWS_SIGNER_SUBJECT`，预期证书的完整 Subject，格式与 `Get-AuthenticodeSignature` 输出一致 |

从钥匙串的「我的证书」导出 Developer ID Application 身份为带密码的 `.p12`。在 App Store Connect 的 Users and Access → Integrations 创建团队 API Key，下载 `.p8`。将密钥和证书存入上表指定的 GitHub 环境 Secrets。CI 使用临时钥匙串导入证书并创建公证配置。证书链缺失时，按 Apple 说明安装匹配的 Developer ID 中间证书。 [App Store Connect 团队 API Key](https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-api/)

Windows 端使用 Artifact Signing 的 **Public Trust** 证书配置。Entra 联合凭据的 GitHub 主体为 `repo:lightzfpwings/pointgroup-reducer:environment:basis-release-signing`。给身份分配签名配置所需的 `Artifact Signing Certificate Profile Signer` 角色。选择服务前请核对身份和地区资格。若使用其他受信任 CA 或硬件密钥，构建器支持在已配置供应商和 Windows SDK SignTool 的签名机器上构建包。

- [Apple Developer ID](https://developer.apple.com/developer-id/)
- [Apple 公证工作流](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)
- [Artifact Signing 资格与配置](https://learn.microsoft.com/azure/artifact-signing/quickstart)
- [Artifact Signing 的 GitHub OIDC 配置](https://github.com/Azure/artifact-signing-action/blob/v2.0.0/docs/OIDC.md)

## 构建与验证

在已配置受信任证书的 Windows x64 机器上，从 Windows 个人证书存储使用证书指纹：

```powershell
python packaging/build_windows.py --with-full --require-signature --sign-thumbprint $thumbprint
```

若签名服务需独立步骤，先用 `--build-only` 生成程序，对 `build/windows-x64/BasisCharacter/` 下的 `BasisCharacter.exe` 和 `BasisCharacter.dll` 签名并加可信时间戳，再用 `--package-only --with-full --require-signature --expected-signer-subject "$subject"` 复验及打包。使用干净的 Windows 信任存储运行校验。

GitHub 的受信任签名发布任务要求两平台的签名报告及包校验全部通过。分支合并且凭据配置完成后，可从 Actions 的 **Integrated basis app checks** 选择 `main` 并启用 `publish`。发布后在使用默认安全策略的另一台 Mac 上实际下载 DMG，拖到「应用程序」并启动。在另一台 Windows 电脑上下载并解压 ZIP，在文件属性的「数字签名」页核对发布者后启动。
