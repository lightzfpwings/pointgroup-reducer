using System.Reflection;
using System.Text;
using System.Text.Json;
using Jint;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace BasisCharacter;

internal static class Program
{
    internal const string Page = "https://basischaracter.local/index.html";
    internal static string Resources => Path.Combine(AppContext.BaseDirectory, "Resources");
    internal static string Version => Assembly.GetExecutingAssembly().GetCustomAttribute<AssemblyInformationalVersionAttribute>()!.InformationalVersion.Split('+')[0];

    [STAThread]
    static int Main(string[] args)
    {
        if (args.Length > 0 && args[0] == "--self-check")
        {
            try
            {
                var report = SelfCheck();
                // WinExe 通过文件提供自检结果，避免依赖控制台附着状态。
                if (args.Length == 2) File.WriteAllText(args[1], report, new UTF8Encoding(false));
                else Console.WriteLine(report);
                return 0;
            }
            catch (Exception e) { Console.Error.WriteLine(e); return 1; }
        }
        ApplicationConfiguration.Initialize();
        Application.Run(new MainWindow());
        return 0;
    }

    private static string SelfCheck()
    {
        var page = File.ReadAllText(Path.Combine(Resources, "index.html"));
        if (!page.Contains("id=\"calculate\"") || page.Contains("<script src=")) throw new InvalidDataException("HTML resources missing");
        // 不授予 CLR/网络/浏览器权限；仅执行随软件附带的数学脚本。
        var engine = new Engine(options => options.TimeoutInterval(TimeSpan.FromMinutes(10)));
        foreach (var name in new[] { "engine.js", "reducer-catalog.js", "reducer-adapter.js", "reduction-catalog.js", "reduction-engine.js", "messages-data.js", "i18n.js", "math-format.js" })
            engine.Execute(File.ReadAllText(Path.Combine(Resources, name)));
        var report = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(engine.Evaluate(File.ReadAllText(Path.Combine(Resources, "self-check.js"))).AsString())!;
        if (report["version"].GetString() != Version || report["reductionVersion"].GetString() != Version) throw new InvalidDataException("Version mismatch");
        Bridge.ValidateSave("basis.json", "{\"ok\":true}");
        foreach (var name in new[] { "../basis.json", "a\\basis.json", "a:stream.json", "CON.json", "basis.txt", "a\n.json" })
        {
            var rejected = false;
            try { Bridge.ValidateSave(name, "{}"); } catch (InvalidDataException) { rejected = true; }
            if (!rejected) throw new InvalidDataException("Invalid name accepted");
        }
        foreach (var text in new[] { "not JSON", "[]", "null" })
        {
            var rejected = false;
            try { Bridge.ValidateSave("basis.json", text); } catch (Exception e) when (e is InvalidDataException or JsonException) { rejected = true; }
            if (!rejected) throw new InvalidDataException("Invalid payload accepted");
        }
        if (!Bridge.TrustedSource(Page, Page) || Bridge.TrustedSource(Page, "https://example.org/") || Bridge.TrustedSource("https://example.org/", Page)) throw new InvalidDataException("Origin guard failed");
        if (!File.Exists(Path.Combine(Resources, "bridge.js"))) throw new InvalidDataException("Bridge missing");
        report["jsonSavePayloadChecks"] = JsonSerializer.SerializeToElement("passed");
        report["originChecks"] = JsonSerializer.SerializeToElement("passed");
        report["resourcesPresent"] = JsonSerializer.SerializeToElement(true);
        return JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true });
    }
}

internal static class Bridge
{
    internal static bool TrustedSource(string source, string current) => source == Program.Page && current == Program.Page;
    internal static byte[] ValidateSave(string name, string text)
    {
        var stem = Path.GetFileNameWithoutExtension(name);
        // Windows 文件名与设备名规则；桥接只传文件名，路径由系统对话框选择。
        if (name.Length == 0 || name.Length > 160 || !name.EndsWith(".json", StringComparison.OrdinalIgnoreCase) || name.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 || name.Any(char.IsControl) ||
            new[] { "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9" }.Contains(stem, StringComparer.OrdinalIgnoreCase))
            throw new InvalidDataException("Invalid filename");
        var data = Encoding.UTF8.GetBytes(text);
        if (data.Length > 128 * 1024 * 1024) throw new InvalidDataException("JSON is too large");
        using var json = JsonDocument.Parse(data);
        if (json.RootElement.ValueKind != JsonValueKind.Object) throw new InvalidDataException("JSON object required");
        return data;
    }
    internal static void AtomicWrite(string path, byte[] data)
    {
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try { File.WriteAllBytes(temporary, data); File.Move(temporary, path, true); }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
}

internal sealed class MainWindow : Form
{
    private readonly WebView2 view = new() { Dock = DockStyle.Fill };
    private readonly MenuStrip menu = new();
    private readonly string dataFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SymmetryGroup", "BasisCharacter");
    private string language = "zh-Hans";
    private string L(string simplified, string traditional, string english) => language == "en" ? english : language == "zh-Hant" ? traditional : simplified;
    private static bool ValidLanguage(string value) => value is "zh-Hans" or "zh-Hant" or "en";
    internal MainWindow()
    {
        try
        {
            var path = Path.Combine(dataFolder, "preferences.json");
            if (File.Exists(path) && new FileInfo(path).Length <= 4096)
            {
                using var preferences = JsonDocument.Parse(File.ReadAllText(path));
                var value = preferences.RootElement.GetProperty("language").GetString();
                if (value != null && ValidLanguage(value)) language = value;
            }
        }
        catch { /* 偏好损坏不会阻止计算；按默认语言启动。 */ }
        ClientSize = new Size(1080, 800); MinimumSize = new Size(740, 580); StartPosition = FormStartPosition.CenterScreen;
        Controls.Add(view); Controls.Add(menu); MainMenuStrip = menu; UpdateMenus();
        Shown += async (_, _) => await InitializeWebView();
    }
    private void UpdateMenus()
    {
        Text = L("点群与基函数", "點群與基函數", "Point Groups & Basis Functions");
        menu.Items.Clear();
        var file = new ToolStripMenuItem(L("文件", "檔案", "File"));
        Add(file, L("新建", "新增", "New"), "new-project", Keys.Control | Keys.N);
        var open = new ToolStripMenuItem(L("载入", "開啟", "Open"), null, async (_, _) => await OpenJSON()) { ShortcutKeys = Keys.Control | Keys.O }; file.DropDownItems.Add(open);
        Add(file, L("保存输入", "儲存輸入", "Save Input"), "save-project", Keys.Control | Keys.S);
        Add(file, L("导出结果", "匯出結果", "Export Results"), "export-result", Keys.Control | Keys.E);
        file.DropDownItems.Add(new ToolStripSeparator()); file.DropDownItems.Add(L("退出", "結束", "Exit"), null, (_, _) => Close()); menu.Items.Add(file);
        var languages = new ToolStripMenuItem(L("语言", "語言", "Language"));
        foreach (var (value, label) in new[] { ("zh-Hans", "简体中文"), ("zh-Hant", "繁體中文"), ("en", "English") })
            languages.DropDownItems.Add(new ToolStripMenuItem(label, null, async (_, _) => await Script("window.BasisDesktop?.setLanguage(" + JsonSerializer.Serialize(value) + ")")) { Checked = language == value });
        menu.Items.Add(languages);
        menu.Items.Add(new ToolStripMenuItem(L("关于", "關於", "About"), null, (_, _) => MessageBox.Show(this, Text + " " + Program.Version, Text)));
    }
    private void Add(ToolStripMenuItem parent, string label, string id, Keys keys) => parent.DropDownItems.Add(new ToolStripMenuItem(label, null, async (_, _) => await Script("document.getElementById(" + JsonSerializer.Serialize(id) + ")?.click()")) { ShortcutKeys = keys });
    private async Task Script(string script)
    {
        try { if (view.CoreWebView2 != null && view.Source?.AbsoluteUri == Program.Page) await view.ExecuteScriptAsync(script); }
        catch (Exception e) { Error(e); }
    }
    private async Task InitializeWebView()
    {
        try
        {
            if (!File.Exists(Path.Combine(Program.Resources, "index.html"))) throw new FileNotFoundException(L("应用资源缺失，请重新解压完整软件包。", "程式資源缺失，請重新解壓完整軟體包。", "Application resources are missing. Extract the complete package again."));
            // 检测运行组件；仅提示用户运行随包安装器，不自动下载或安装。
            try { _ = CoreWebView2Environment.GetAvailableBrowserVersionString(); }
            catch (WebView2RuntimeNotFoundException)
            {
                MessageBox.Show(this, L("请先运行同文件夹中的 MicrosoftEdgeWebView2RuntimeInstallerX64.exe，安装完成后重新打开软件。安装器可离线运行。", "請先執行同資料夾中的 MicrosoftEdgeWebView2RuntimeInstallerX64.exe，安裝完成後重新開啟軟體。安裝器可離線執行。", "Run MicrosoftEdgeWebView2RuntimeInstallerX64.exe in this folder, then reopen the app. The installer works offline."), Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
                Close(); return;
            }
            Directory.CreateDirectory(dataFolder);
            var environment = await CoreWebView2Environment.CreateAsync(userDataFolder: Path.Combine(dataFolder, "WebView2"));
            await view.EnsureCoreWebView2Async(environment);
            var core = view.CoreWebView2;
            core.SetVirtualHostNameToFolderMapping("basischaracter.local", Program.Resources, CoreWebView2HostResourceAccessKind.DenyCors);
            core.Settings.AreDefaultContextMenusEnabled = false;
            core.Settings.AreDevToolsEnabled = false;
            core.Settings.AreBrowserAcceleratorKeysEnabled = false;
            core.Settings.IsStatusBarEnabled = false;
            core.NavigationStarting += (_, e) => { if (e.Uri != Program.Page) e.Cancel = true; };
            core.FrameNavigationStarting += (_, e) => e.Cancel = true;
            core.NewWindowRequested += (_, e) => e.Handled = true;
            core.DownloadStarting += (_, e) => e.Cancel = true;
            core.PermissionRequested += (_, e) => e.State = CoreWebView2PermissionState.Deny;
            core.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All);
            core.WebResourceRequested += (_, e) => { if (e.Request.Uri != Program.Page) e.Response = environment.CreateWebResourceResponse(Stream.Null, 403, "Forbidden", "Content-Type: text/plain"); };
            core.WebMessageReceived += async (_, e) => await Receive(e);
            await core.AddScriptToExecuteOnDocumentCreatedAsync("window.BasisPreferredLanguage=" + JsonSerializer.Serialize(language) + ";\n" + File.ReadAllText(Path.Combine(Program.Resources, "bridge.js")));
            view.Source = new Uri(Program.Page);
        }
        catch (Exception e) { Error(e); Close(); }
    }
    private async Task Receive(CoreWebView2WebMessageReceivedEventArgs message)
    {
        if (!Bridge.TrustedSource(message.Source, view.Source?.AbsoluteUri ?? "")) return;
        try
        {
            using var json = JsonDocument.Parse(message.WebMessageAsJson);
            var type = json.RootElement.GetProperty("type").GetString();
            var payload = json.RootElement.GetProperty("payload");
            switch (type)
            {
                case "openJSON": await OpenJSON(); break;
                case "saveJSON":
                    var name = payload.GetProperty("name").GetString()!;
                    var text = payload.GetProperty("text").GetString()!;
                    var data = Bridge.ValidateSave(name, text);
                    using (var dialog = new SaveFileDialog { Title = L("保存 JSON", "儲存 JSON", "Save JSON"), Filter = "JSON (*.json)|*.json", DefaultExt = "json", AddExtension = true, FileName = name })
                        if (dialog.ShowDialog(this) == DialogResult.OK) Bridge.AtomicWrite(dialog.FileName, data);
                    break;
                case "copyText":
                    var copy = payload.GetProperty("text").GetString()!;
                    if (Encoding.UTF8.GetByteCount(copy) > 8 * 1024 * 1024) throw new InvalidDataException("Text is too large");
                    if (copy.Length > 0) Clipboard.SetText(copy);
                    break;
                case "languageChanged":
                    var value = payload.GetProperty("language").GetString()!;
                    if (!ValidLanguage(value)) return;
                    language = value; UpdateMenus();
                    Bridge.AtomicWrite(Path.Combine(dataFolder, "preferences.json"), JsonSerializer.SerializeToUtf8Bytes(new { language }));
                    break;
            }
        }
        catch (Exception e) { Error(e); }
    }
    private async Task OpenJSON()
    {
        if (view.CoreWebView2 == null || view.Source?.AbsoluteUri != Program.Page) return;
        try
        {
            using var dialog = new OpenFileDialog { Title = L("载入计算输入", "開啟計算輸入", "Open Calculation Input"), Filter = "JSON (*.json)|*.json", Multiselect = false };
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            if (new FileInfo(dialog.FileName).Length > 2 * 1024 * 1024) throw new InvalidDataException(L("输入文件超过 2 MiB。", "輸入檔案超過 2 MiB。", "Input file exceeds 2 MiB."));
            var text = File.ReadAllText(dialog.FileName, new UTF8Encoding(false, true));
            using var json = JsonDocument.Parse(text);
            if (json.RootElement.ValueKind != JsonValueKind.Object) throw new InvalidDataException("JSON object required");
            await Script("window.BasisDesktop.importJSON(" + JsonSerializer.Serialize(text) + ")");
        }
        catch (Exception e) { Error(e); }
    }
    private void Error(Exception e) => MessageBox.Show(this, e.Message, L("操作未完成", "操作未完成", "Action could not be completed"), MessageBoxButtons.OK, MessageBoxIcon.Error);
}
