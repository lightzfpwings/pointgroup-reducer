# Windows x64 packaging

Build on native Windows x64 with Python 3.12 and .NET 10 SDK:

    python packaging/build_windows.py

Add `--with-full` to also build the complete archive with three language-specific HTML files and Microsoft's offline installer. The builder verifies the installer signature before packaging it.

The lightweight ZIP includes .NET, a trilingual offline HTML page, JSON examples, and a calculation self-check. Extract the entire ZIP and launch `BasisCharacter.exe`. If WebView2 is missing, open `Download-WebView2.url`, download the Evergreen Standalone Installer for x64, install it, then reopen the app. Copy the installer from an online computer for offline deployment. [Microsoft WebView2 downloads](https://developer.microsoft.com/microsoft-edge/webview2/#download)

Four existing desktop operations are bridged through top-level WebView2 messages. Both the document source and current navigation must equal the packaged virtual page; all other navigations, frames, requests, popups and downloads are blocked. Input limits and native JSON validation match the Mac package. Preferences live under LocalAppData/SymmetryGroup/BasisCharacter.

The builder runs the shared calculation self-check in Jint and writes its report and SHA-256 checksums to `dist/`. The application executable is not Authenticode signed.

Runtime distribution: [Microsoft WebView2 offline deployment](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution#offline-deployment).
Supported systems: [Microsoft .NET Windows support](https://learn.microsoft.com/en-us/dotnet/core/install/windows#supported-versions).
SDK: [Microsoft.Web.WebView2 1.0.4258.31](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4258.31).
Calculation self-check interpreter: [Jint](https://github.com/sebastienros/jint), without browser packages or CLR access. NuGet license files are copied to the distribution.
