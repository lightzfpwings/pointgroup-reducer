# Windows x64 packaging

Build on native Windows x64 with Python 3.12 and .NET 10 SDK:

    python packaging/build_windows.py

The bundle includes .NET, the common trilingual HTML, JSON examples, a pure-calculation self-check, and Microsoft's signed full offline WebView2 installer. It does not automatically install the runtime or download anything at application startup. Extract the entire ZIP and launch BasisCharacter.exe. When the runtime is absent, run the bundled installer and reopen the app.

Four existing desktop operations are bridged through top-level WebView2 messages. Both the document source and current navigation must equal the packaged virtual page; all other navigations, frames, requests, popups and downloads are blocked. Input limits and native JSON validation match the Mac package. Preferences live under LocalAppData/SymmetryGroup/BasisCharacter.

The builder validates Microsoft Authenticode signatures, checks pure ECMAScript mathematics using Jint, and emits SHA-256 checksums. No browser DOM or UI rendering is used by the self-check. Native window rendering, keyboard interaction and dialogs need actual Windows user testing. The application executable is not Authenticode signed.

Runtime distribution: [Microsoft WebView2 offline deployment](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution#offline-deployment).
Supported systems: [Microsoft .NET Windows support](https://learn.microsoft.com/en-us/dotnet/core/install/windows#supported-versions).
SDK: [Microsoft.Web.WebView2 1.0.4258.31](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4258.31).
Calculation self-check interpreter: [Jint](https://github.com/sebastienros/jint), without browser packages or CLR access. NuGet license files are copied to the distribution.
