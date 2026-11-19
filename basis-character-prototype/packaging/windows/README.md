# Windows x64 packaging

Build on native Windows x64 with Python 3.12 and .NET 10 SDK:

    python packaging/build_windows.py

Add `--with-full` to also build the complete archive with three language-specific HTML files and Microsoft's offline installer. The builder verifies the installer signature before packaging it.

The lightweight ZIP includes .NET, a trilingual offline HTML page, JSON examples, and a calculation self-check. Extract the entire ZIP and launch `BasisCharacter.exe`. If WebView2 is missing, open `Download-WebView2.url`, download the Evergreen Standalone Installer for x64, install it, then reopen the app. Copy the installer from an online computer for offline deployment. [Microsoft WebView2 downloads](https://developer.microsoft.com/microsoft-edge/webview2/#download)

Four existing desktop operations are bridged through top-level WebView2 messages. Both the document source and current navigation must equal the packaged virtual page; all other navigations, frames, requests, popups and downloads are blocked. Input limits and native JSON validation match the Mac package. Preferences live under LocalAppData/SymmetryGroup/BasisCharacter.

The builder runs the shared calculation self-check in Jint and writes its report and SHA-256 checksums to `dist/`. The default build is an unsigned development build. Public releases can use the signing flows below. Signing establishes the publisher and protects file integrity; SmartScreen can still warn while a new release or publisher builds reputation. [Microsoft SmartScreen reputation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)

## Signed builds

Build first, sign **both** `BasisCharacter.exe` and `BasisCharacter.dll` in `build/windows-x64/BasisCharacter`, then verify and package in the same workspace:

    python packaging/build_windows.py --build-only
    # Sign the two binaries using the approved signing service.
    python packaging/build_windows.py --package-only --with-full --require-signature --expected-signer-subject "CN=Your exact validated publisher subject"

`--package-only` never invokes `dotnet publish` or replaces signed binaries. Use the complete Subject returned by `Get-AuthenticodeSignature`, rather than a substring or display name. The GitHub signing workflow uses Azure Artifact Signing with SHA-256 and RFC3161 timestamps. It requires an eligible validated identity and a Public Trust profile; no signing service or identity is provisioned by this repository. [Microsoft signing integrations](https://learn.microsoft.com/en-us/azure/artifact-signing/how-to-signing-integrations)

For an existing CA certificate in a configured Windows certificate provider, the optional local interface is `--sign-thumbprint <40-hex>` and, for `LocalMachine\My`, `--sign-machine-store`. It uses SignTool with SHA-256 and a timestamp, then performs the same verification. `SIGNTOOL_PATH` may identify the installed Windows SDK executable. Private keys remain with the provider; this builder accepts no PFX or passwords and never changes trusted roots. See the shared [signing setup](../../SIGNING.md) for credentials and provider configuration.

Verification requires a valid embedded Authenticode signature, timestamp and expected publisher for both application binaries before any ZIP is generated. SignTool applies Windows Authenticode policy and verifies all embedded signatures; catalog-only results and self-signed publisher certificates are rejected. Trust follows the signing machine's Windows configuration, so use a clean, controlled environment with normal public roots. Reports include publisher/timestamp certificates and final binary hashes. Third-party runtime signatures are not replaced. [SignTool](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool)

Portable safety checks (signing arguments and packaging failure behavior):

    python -m unittest discover -s packaging/windows -p test_authenticode.py

These checks do not replace a Windows build with a real trusted certificate, timestamp service, and clean downloaded-app test. A signed release should also be extracted and checked on Windows before publication.

Runtime distribution: [Microsoft WebView2 offline deployment](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution#offline-deployment).
Supported systems: [Microsoft .NET Windows support](https://learn.microsoft.com/en-us/dotnet/core/install/windows#supported-versions).
SDK: [Microsoft.Web.WebView2 1.0.4258.31](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4258.31).
Calculation self-check interpreter: [Jint](https://github.com/sebastienros/jint), without browser packages or CLR access. NuGet license files are copied to the distribution.
