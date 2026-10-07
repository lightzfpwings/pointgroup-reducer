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
          let engine = Bundle.main.url(forResource: "engine", withExtension: "js"),
          let catalog = Bundle.main.url(forResource: "reducer-catalog", withExtension: "js"),
          let adapter = Bundle.main.url(forResource: "reducer-adapter", withExtension: "js") else {
        throw PackageError.invalidResource
    }
    let page = try String(contentsOf: html, encoding: .utf8)
    guard page.contains("id=\"calculate\""), !page.contains("<script src=") else {
        throw PackageError.invalidResource
    }
    guard let context = JSContext() else { throw PackageError.engineFailure("No JSContext") }
    context.evaluateScript(try String(contentsOf: engine, encoding: .utf8))
    context.evaluateScript(try String(contentsOf: catalog, encoding: .utf8))
    context.evaluateScript(try String(contentsOf: adapter, encoding: .utf8))
    for name in ["reduction-catalog", "reduction-engine", "messages-data", "i18n", "math-format"] {
        guard let url = Bundle.main.url(forResource: name, withExtension: "js") else { throw PackageError.invalidResource }
        context.evaluateScript(try String(contentsOf: url, encoding: .utf8))
        if let exception = context.exception { throw PackageError.engineFailure(exception.toString()) }
    }
    if let exception = context.exception { throw PackageError.engineFailure(exception.toString()) }
    let script = """
    JSON.stringify(['benzene','water','central-c2v','central-oh','icosahedron','central-d-c2v','central-d-oh'].map(name => {
      const r = BasisEngine.calculate(BasisEngine.template(name));
      const reduced = ReductionEngine.integrate(r, ReducerAdapter);
      return {name, dimension:r.dimension, blocks:r.blocks.length, characters:r.totalCharacters, checks:r.checks,
              reduced:reduced.total.valid, terms:reduced.total.terms, reductionResidual:reduced.total.integer_residual};
    }))
    """
    guard let output = context.evaluateScript(script)?.toString(), context.exception == nil,
          let data = output.data(using: .utf8),
          let results = try JSONSerialization.jsonObject(with: data) as? [[String: Any]],
          results.count == 7 else { throw PackageError.engineFailure(context.exception?.toString() ?? "No results") }
    let expectedDimensions = [30, 2, 3, 3, 12, 5, 5]
    let expectedBlocks = [4, 1, 3, 1, 1, 5, 2]
    for (i, result) in results.enumerated() {
        guard result["dimension"] as? Int == expectedDimensions[i],
              result["blocks"] as? Int == expectedBlocks[i] else {
            throw PackageError.engineFailure("Example mismatch")
        }
        guard result["reduced"] as? Bool == true else { throw PackageError.engineFailure("Reduction failed") }
    }
    guard let benzene = results[0]["characters"] as? [Int],
          benzene == [30,0,0,0,2,0,0,0,0,18,0,6] else {
        throw PackageError.engineFailure("Benzene characters mismatch")
    }
    let allGroups = """
    JSON.stringify(BasisEngine.groupNames.map(name => {
      const g = BasisEngine.group(name);
      const pInput = BasisEngine.template('central-c2v'); pInput.group = name;
      const dInput = BasisEngine.template('central-d-oh'); dInput.group = name;
      const p = BasisEngine.calculate(pInput), d = BasisEngine.calculate(dInput), aligned = ReducerAdapter.align(d);
      // 完整 d 的独立检验式：χ₂(R) = [(tr R)² + tr(R²)]/2 − 1。
      const traces = g.classes.map(c => {
        const m = g.matrices[c.representative], square = BasisEngine.matmul(m,m);
        const tr = m[0][0]+m[1][1]+m[2][2];
        return (tr*tr+square[0][0]+square[1][1]+square[2][2])/2-1;
      });
      const error = Math.max(...traces.map((v,i)=>Math.abs(v-d.totalCharacters[i])));
      return {group:name, order:g.size, classes:g.classes.length, dimension:p.dimension, dDimension:d.dimension,
              representationError:Math.max(p.checks.representationError,d.checks.representationError),
              dTraceError:error, alignedClasses:aligned.classes.length};
    }))
    """
    guard let groupsText = context.evaluateScript(allGroups)?.toString(), context.exception == nil,
          let groupsData = groupsText.data(using: .utf8),
          let groups = try JSONSerialization.jsonObject(with: groupsData) as? [[String: Any]], groups.count == 87,
          context.evaluateScript("BasisEngine.VERSION")?.toString() == Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String else {
        throw PackageError.engineFailure(context.exception?.toString() ?? "Expanded groups/version mismatch")
    }
    guard groups.allSatisfy({ ($0["dimension"] as? Int) == 3 && ($0["dDimension"] as? Int) == 5 &&
        ($0["representationError"] as? Double ?? 1) < 1e-7 && ($0["dTraceError"] as? Double ?? 1) < 1e-7 &&
        ($0["classes"] as? Int) == ($0["alignedClasses"] as? Int) }) else {
        throw PackageError.engineFailure("Expanded group representation mismatch")
    }
    let integratedScript = """
    JSON.stringify({tables:ReductionEngine.groupNames.map(name=>{
      const t=ReductionEngine.table(name),r=ReductionEngine.reduce(name,t.X[0]);
      if(!r.valid||r.integer_a[0]!==1)throw Error(name);
      return {group:name,classes:t.classes.length,orthogonalityError:t.orthogonalityError};
    }),languages:I18n.languages.map(language=>{I18n.setLanguage(language);return {language,title:I18n.translate('点群与基函数')};}),
    parser:ReductionEngine.number('sqrt(3)/2'),integrated:true})
    """
    guard let integrationText = context.evaluateScript(integratedScript)?.toString(), context.exception == nil,
          let integrationData = integrationText.data(using: .utf8),
          let integration = try JSONSerialization.jsonObject(with: integrationData) as? [String: Any],
          let tables = integration["tables"] as? [[String: Any]], tables.count == 423,
          let languages = integration["languages"] as? [[String: Any]], languages.count == 3,
          languages[2]["title"] as? String == "Point Groups & Basis Functions" else {
        throw PackageError.engineFailure(context.exception?.toString() ?? "Integration or language mismatch")
    }
    _ = try jsonPayload(name: "basis.json", text: "{\"ok\":true}")
    do { _ = try jsonPayload(name: "../basis.json", text: "{}"); throw PackageError.engineFailure("Invalid filename accepted") }
    catch PackageError.invalidName { }
    do { _ = try jsonPayload(name: "basis.json", text: "not json"); throw PackageError.engineFailure("Invalid JSON accepted") }
    catch PackageError.invalidJSON { }
    let report: [String: Any] = [
        "status": "passed", "runtime": "Apple JavaScriptCore", "examples": results,
        "supportedPointGroups": groups.count, "expandedGroupChecks": groups,
        "jsonSavePayloadChecks": "passed", "resourcesPresent": true,
        "uiLaunched": false, "reductionIntegrated": true, "reductionTables": tables, "languages": languages
    ]
    let reportData = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
    FileHandle.standardOutput.write(reportData)
    FileHandle.standardOutput.write(Data("\n".utf8))
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
    private var window: NSWindow!
    private var webView: WKWebView!
    private var contentURL: URL!
    private var language = UserDefaults.standard.string(forKey: "symmetry-language") ?? "zh-Hans"
    private func l(_ simplified: String, _ traditional: String, _ english: String) -> String {
        language == "en" ? english : language == "zh-Hant" ? traditional : simplified
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        guard let resource = Bundle.main.url(forResource: "index", withExtension: "html") else {
            showError(l("应用资源缺失，请重新解压完整应用。", "應用程式資源缺失，請重新解壓完整程式。", "Application resources are missing. Extract the complete app again."))
            NSApp.terminate(nil); return
        }
        contentURL = resource.standardizedFileURL
        if !["zh-Hans", "zh-Hant", "en"].contains(language) { language = "zh-Hans" }
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.userContentController.add(self, name: "saveJSON")
        configuration.userContentController.add(self, name: "openJSON")
        configuration.userContentController.add(self, name: "copyText")
        configuration.userContentController.add(self, name: "languageChanged")
        configuration.userContentController.addUserScript(WKUserScript(source: "window.BasisPreferredLanguage='\(language)';", injectionTime: .atDocumentStart, forMainFrameOnly: true))
        webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1080, height: 800),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable],
                          backing: .buffered, defer: false)
        window.title = l("点群与基函数", "點群與基函數", "Point Groups & Basis Functions")
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
        let appItem = NSMenuItem(); bar.addItem(appItem)
        let appMenu = NSMenu(title: l("点群与基函数", "點群與基函數", "Point Groups & Basis Functions")); appItem.submenu = appMenu
        let about = NSMenuItem(title: l("关于点群与基函数", "關於點群與基函數", "About Point Groups & Basis Functions"), action: #selector(showAbout), keyEquivalent: ""); about.target = self; appMenu.addItem(about)
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: l("退出", "結束", "Quit"), action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        let fileItem = NSMenuItem(); bar.addItem(fileItem)
        let fileMenu = NSMenu(title: l("文件", "檔案", "File")); fileItem.submenu = fileMenu
        for (title, action, key) in [(l("新建", "新增", "New"), #selector(newProject), "n"), (l("载入", "開啟", "Open"), #selector(loadProject), "o"), (l("保存输入", "儲存輸入", "Save Input"), #selector(saveProject), "s"), (l("导出结果", "匯出結果", "Export Results"), #selector(exportResult), "e")] {
            let item = NSMenuItem(title: title, action: action, keyEquivalent: key); item.target = self; fileMenu.addItem(item)
        }
        let editItem = NSMenuItem(); bar.addItem(editItem)
        let editMenu = NSMenu(title: l("编辑", "編輯", "Edit")); editItem.submenu = editMenu
        for (title, action, key) in [(l("剪切", "剪下", "Cut"), #selector(NSText.cut(_:)), "x"), (l("复制", "複製", "Copy"), #selector(NSText.copy(_:)), "c"), (l("粘贴", "貼上", "Paste"), #selector(NSText.paste(_:)), "v"), (l("全选", "全選", "Select All"), #selector(NSText.selectAll(_:)), "a")] {
            editMenu.addItem(withTitle: title, action: action, keyEquivalent: key)
        }
        let languageItem = NSMenuItem(); bar.addItem(languageItem)
        let languageMenu = NSMenu(title: l("语言", "語言", "Language")); languageItem.submenu = languageMenu
        for (value, title) in [("zh-Hans", "简体中文"), ("zh-Hant", "繁體中文"), ("en", "English")] {
            let item = NSMenuItem(title: title, action: #selector(changeLanguage(_:)), keyEquivalent: "")
            item.target = self; item.representedObject = value; item.state = language == value ? .on : .off; languageMenu.addItem(item)
        }
        NSApp.mainMenu = bar
    }
    @objc private func showAbout() {
        NSApp.orderFrontStandardAboutPanel(options: [.applicationName: l("点群与基函数", "點群與基函數", "Point Groups & Basis Functions"), .applicationVersion: "0.4.2"])
    }
    @objc private func changeLanguage(_ sender: NSMenuItem) {
        guard let value = sender.representedObject as? String, ["zh-Hans", "zh-Hant", "en"].contains(value) else { return }
        webView.evaluateJavaScript("window.BasisDesktop.setLanguage('\(value)')", completionHandler: nil)
    }

    private func clickControl(_ id: String) {
        webView.evaluateJavaScript("document.getElementById('\(id)')?.click()", completionHandler: nil)
    }
    @objc private func newProject() { clickControl("new-project") }
    @objc private func loadProject() { presentOpenPanel() }
    @objc private func saveProject() { clickControl("save-project") }
    @objc private func exportResult() { clickControl("export-result") }

    private func presentOpenPanel() {
        let panel = NSOpenPanel()
        panel.title = l("载入计算输入", "開啟計算輸入", "Open Calculation Input")
        panel.allowedContentTypes = [.json]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.beginSheetModal(for: window) { response in
            guard response == .OK, let url = panel.url else { return }
            do {
                let size = try url.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
                guard size <= 2 * 1024 * 1024 else { self.showError(self.l("输入文件不能超过 2 MiB。", "輸入檔案不能超過 2 MiB。", "Input file cannot exceed 2 MiB.")); return }
                let text = try String(contentsOf: url, encoding: .utf8)
                let argument = try JSONSerialization.data(withJSONObject: [text], options: [])
                guard let encoded = String(data: argument, encoding: .utf8) else { return }
                self.webView.evaluateJavaScript("window.BasisDesktop.importJSON(\(encoded)[0])") { _, error in
                    if let error { self.showError(self.l("载入失败：", "開啟失敗：", "Open failed: ") + error.localizedDescription) }
                }
            } catch { self.showError(self.l("载入失败：", "開啟失敗：", "Open failed: ") + error.localizedDescription) }
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
        let panel = NSOpenPanel()
        panel.title = l("载入计算输入", "開啟計算輸入", "Open Calculation Input")
        panel.allowedContentTypes = [.json]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.beginSheetModal(for: window) { response in completionHandler(response == .OK ? panel.urls : nil) }
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.frameInfo.isMainFrame,
              message.frameInfo.request.url?.standardizedFileURL == contentURL else { return }
        if message.name == "openJSON" { presentOpenPanel(); return }
        if message.name == "languageChanged", let body = message.body as? [String: Any], let value = body["language"] as? String, ["zh-Hans", "zh-Hant", "en"].contains(value) {
            language = value; UserDefaults.standard.set(value, forKey: "symmetry-language")
            window.title = l("点群与基函数", "點群與基函數", "Point Groups & Basis Functions"); installMenu(); return
        }
        if message.name == "copyText", let body = message.body as? [String: Any], let text = body["text"] as? String, text.utf8.count <= 8 * 1024 * 1024 {
            NSPasteboard.general.clearContents(); NSPasteboard.general.setString(text, forType: .string); return
        }
        guard message.name == "saveJSON", let body = message.body as? [String: Any],
              let name = body["name"] as? String, let text = body["text"] as? String else { return }
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

    private func showError(_ message: String) {
        let alert = NSAlert(); alert.messageText = l("点群与基函数", "點群與基函數", "Point Groups & Basis Functions"); alert.informativeText = message
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
