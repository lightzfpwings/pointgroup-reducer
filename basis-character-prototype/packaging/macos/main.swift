import Cocoa
import WebKit
import JavaScriptCore
import UniformTypeIdentifiers

enum PackageError: Error {
    case invalidJSON, invalidName, invalidResource, engineFailure(String)
}

func jsonPayload(name: String, text: String) throws -> Data {
    guard name.hasSuffix(".json"), !name.contains("/"), !name.contains("\\"),
          !name.contains("\n"), name.count <= 160 else { throw PackageError.invalidName }
    let data = Data(text.utf8)
    guard data.count <= 128 * 1024 * 1024,
          (try? JSONSerialization.jsonObject(with: data)) is [String: Any] else {
        throw PackageError.invalidJSON
    }
    return data
}

// Headless verification uses JavaScriptCore, not a browser or desktop UI.
func selfCheck() throws {
    guard let html = Bundle.main.url(forResource: "index", withExtension: "html"),
          let checks = Bundle.main.url(forResource: "self-check", withExtension: "js"),
          let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String else {
        throw PackageError.invalidResource
    }
    let page = try String(contentsOf: html, encoding: .utf8)
    guard page.contains("id=\"calculate\""), !page.contains("<script src="),
          let start = page.range(of: "<script data-basis-core>"),
          let end = page.range(of: "</script>", range: start.upperBound..<page.endIndex) else {
        throw PackageError.invalidResource
    }
    guard let context = JSContext() else { throw PackageError.engineFailure("No JSContext") }
    context.evaluateScript(String(page[start.upperBound..<end.lowerBound]))
    if let exception = context.exception { throw PackageError.engineFailure(exception.toString()) }
    let script = try String(contentsOf: checks, encoding: .utf8)
    guard let output = context.evaluateScript(script)?.toString(), context.exception == nil,
          var report = try JSONSerialization.jsonObject(with: Data(output.utf8)) as? [String: Any],
          report["status"] as? String == "passed",
          report["version"] as? String == version,
          report["reductionVersion"] as? String == version else {
        throw PackageError.engineFailure(context.exception?.toString() ?? "Invalid self-check report")
    }
    _ = try jsonPayload(name: "basis.json", text: "{\"ok\":true}")
    do { _ = try jsonPayload(name: "../basis.json", text: "{}"); throw PackageError.engineFailure("Invalid filename accepted") }
    catch PackageError.invalidName { }
    do { _ = try jsonPayload(name: "basis.json", text: "not json"); throw PackageError.engineFailure("Invalid JSON accepted") }
    catch PackageError.invalidJSON { }
    report["runtime"] = "Apple JavaScriptCore"
    report["jsonSavePayloadChecks"] = "passed"
    report["resourcesPresent"] = true
    let reportData = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
    FileHandle.standardOutput.write(reportData)
    FileHandle.standardOutput.write(Data("\n".utf8))
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
    private enum BridgeMessage: String, CaseIterable {
        case saveJSON, openJSON, copyText, languageChanged
    }

    private var window: NSWindow!
    private var webView: WKWebView!
    private var contentURL: URL!
    private var language = UserDefaults.standard.string(forKey: "symmetry-language") ?? "zh-Hans"
    private let languages = [("zh-Hans", "简体中文"), ("zh-Hant", "繁體中文"), ("en", "English")]
    private var appName: String { l("点群与基函数", "點群與基函數", "Point Groups & Basis Functions") }

    private func l(_ simplified: String, _ traditional: String, _ english: String) -> String {
        language == "en" ? english : language == "zh-Hant" ? traditional : simplified
    }

    private func supportsLanguage(_ value: String) -> Bool {
        languages.contains { $0.0 == value }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        guard let resource = Bundle.main.url(forResource: "index", withExtension: "html") else {
            showError(l("应用资源缺失，请重新解压完整应用。", "應用程式資源缺失，請重新解壓完整程式。", "Application resources are missing. Extract the complete app again."))
            NSApp.terminate(nil); return
        }
        contentURL = resource.standardizedFileURL
        if !supportsLanguage(language) { language = "zh-Hans" }
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        for message in BridgeMessage.allCases {
            configuration.userContentController.add(self, name: message.rawValue)
        }
        configuration.userContentController.addUserScript(WKUserScript(source: "window.BasisPreferredLanguage='\(language)';", injectionTime: .atDocumentStart, forMainFrameOnly: true))
        webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1080, height: 800),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable],
                          backing: .buffered, defer: false)
        window.title = appName
        window.minSize = NSSize(width: 740, height: 580)
        window.contentView = webView
        window.isReleasedWhenClosed = false
        window.center()
        installMenu()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        webView.loadFileURL(contentURL, allowingReadAccessTo: contentURL)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    private func installMenu() {
        let bar = NSMenu()
        func addMenu(_ title: String) -> NSMenu {
            let item = NSMenuItem()
            bar.addItem(item)
            let menu = NSMenu(title: title)
            item.submenu = menu
            return menu
        }

        let appMenu = addMenu(appName)
        let about = NSMenuItem(title: l("关于点群与基函数", "關於點群與基函數", "About Point Groups & Basis Functions"), action: #selector(showAbout), keyEquivalent: ""); about.target = self; appMenu.addItem(about)
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: l("退出", "結束", "Quit"), action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        let fileMenu = addMenu(l("文件", "檔案", "File"))
        for (title, action, key) in [(l("新建", "新增", "New"), #selector(newProject), "n"), (l("载入", "開啟", "Open"), #selector(loadProject), "o"), (l("保存输入", "儲存輸入", "Save Input"), #selector(saveProject), "s"), (l("导出结果", "匯出結果", "Export Results"), #selector(exportResult), "e")] {
            let item = NSMenuItem(title: title, action: action, keyEquivalent: key); item.target = self; fileMenu.addItem(item)
        }
        let editMenu = addMenu(l("编辑", "編輯", "Edit"))
        for (title, action, key) in [(l("剪切", "剪下", "Cut"), #selector(NSText.cut(_:)), "x"), (l("复制", "複製", "Copy"), #selector(NSText.copy(_:)), "c"), (l("粘贴", "貼上", "Paste"), #selector(NSText.paste(_:)), "v"), (l("全选", "全選", "Select All"), #selector(NSText.selectAll(_:)), "a")] {
            editMenu.addItem(withTitle: title, action: action, keyEquivalent: key)
        }
        let languageMenu = addMenu(l("语言", "語言", "Language"))
        for (value, title) in languages {
            let item = NSMenuItem(title: title, action: #selector(changeLanguage(_:)), keyEquivalent: "")
            item.target = self; item.representedObject = value; item.state = language == value ? .on : .off; languageMenu.addItem(item)
        }
        NSApp.mainMenu = bar
    }
    @objc private func showAbout() {
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? ""
        NSApp.orderFrontStandardAboutPanel(options: [.applicationName: appName, .applicationVersion: version])
    }
    @objc private func changeLanguage(_ sender: NSMenuItem) {
        guard let value = sender.representedObject as? String, supportsLanguage(value) else { return }
        webView.evaluateJavaScript("window.BasisDesktop.setLanguage('\(value)')", completionHandler: nil)
    }

    private func clickControl(_ id: String) {
        webView.evaluateJavaScript("document.getElementById('\(id)')?.click()", completionHandler: nil)
    }
    @objc private func newProject() { clickControl("new-project") }
    @objc private func loadProject() { presentOpenPanel() }
    @objc private func saveProject() { clickControl("save-project") }
    @objc private func exportResult() { clickControl("export-result") }

    private func chooseJSON(_ completion: @escaping ([URL]?) -> Void) {
        let panel = NSOpenPanel()
        panel.title = l("载入计算输入", "開啟計算輸入", "Open Calculation Input")
        panel.allowedContentTypes = [.json]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.beginSheetModal(for: window) { response in
            completion(response == .OK ? panel.urls : nil)
        }
    }

    private func presentOpenPanel() {
        chooseJSON { urls in
            guard let url = urls?.first else { return }
            do {
                let size = try url.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
                guard size <= 2 * 1024 * 1024 else { self.showError(self.l("输入文件不能超过 2 MiB。", "輸入檔案不能超過 2 MiB。", "Input file cannot exceed 2 MiB.")); return }
                let text = try String(contentsOf: url, encoding: .utf8)
                let argument = try JSONSerialization.data(withJSONObject: [text], options: [])
                guard let encoded = String(data: argument, encoding: .utf8) else { return }
                self.webView.evaluateJavaScript("window.BasisDesktop.importJSON(\(encoded)[0])") { _, error in
                    if let error { self.showOpenError(error) }
                }
            } catch { self.showOpenError(error) }
        }
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url, url.isFileURL,
              url.standardizedFileURL == contentURL else { decisionHandler(.cancel); return }
        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        chooseJSON(completionHandler)
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.frameInfo.isMainFrame,
              message.frameInfo.request.url?.standardizedFileURL == contentURL,
              let command = BridgeMessage(rawValue: message.name) else { return }
        let body = message.body as? [String: Any]
        switch command {
        case .openJSON:
            presentOpenPanel()
        case .languageChanged:
            guard let value = body?["language"] as? String, supportsLanguage(value) else { return }
            language = value
            UserDefaults.standard.set(value, forKey: "symmetry-language")
            window.title = appName
            installMenu()
        case .copyText:
            guard let text = body?["text"] as? String, text.utf8.count <= 8 * 1024 * 1024 else { return }
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(text, forType: .string)
        case .saveJSON:
            guard let name = body?["name"] as? String, let text = body?["text"] as? String else { return }
            presentSavePanel(name: name, text: text)
        }
    }

    private func presentSavePanel(name: String, text: String) {
        do {
            let data = try jsonPayload(name: name, text: text)
            let panel = NSSavePanel()
            panel.title = l("保存 JSON", "儲存 JSON", "Save JSON")
            panel.nameFieldStringValue = name
            panel.allowedContentTypes = [.json]
            panel.canCreateDirectories = true
            panel.beginSheetModal(for: window) { response in
                guard response == .OK, let url = panel.url else { return }
                do { try data.write(to: url, options: .atomic) }
                catch { self.showError(self.l("保存失败：", "儲存失敗：", "Save failed: ") + error.localizedDescription) }
            }
        } catch { showError(l("导出数据无效：", "匯出資料無效：", "Invalid export data: ") + error.localizedDescription) }
    }

    private func showOpenError(_ error: Error) {
        showError(l("载入失败：", "開啟失敗：", "Open failed: ") + error.localizedDescription)
    }

    private func showError(_ message: String) {
        let alert = NSAlert(); alert.messageText = appName; alert.informativeText = message
        if let window { alert.beginSheetModal(for: window) } else { alert.runModal() }
    }
}

@main
struct Launcher {
    @MainActor
    static func main() {
        if CommandLine.arguments.contains("--self-check") {
            do { try selfCheck(); exit(0) }
            catch { FileHandle.standardError.write(Data("Self-check failed: \(error)\n".utf8)); exit(1) }
        } else {
            let app = NSApplication.shared
            let delegate = AppDelegate()
            app.delegate = delegate
            app.setActivationPolicy(.regular)
            withExtendedLifetime(delegate) { app.run() }
        }
    }
}
