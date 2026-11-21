using System.Diagnostics;
using System.IO.Compression;
using System.Net;
using System.Net.Http;
using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace BasisCharacter;

internal static class Updates
{
    private const string Repository = "lightzfpwings/pointgroup-reducer";
    private const string Api = "https://api.github.com/repos/" + Repository + "/releases";
    private const string Inventory = "basis-package-files.json";
    private static readonly HttpClient Client = new(new HttpClientHandler { AllowAutoRedirect = false })
        { Timeout = TimeSpan.FromMinutes(15) };
    private static Version Number(string s) => Regex.IsMatch(s, @"\A(0|[1-9]\d{0,5})\.(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})\z")
        ? Version.Parse(s) : throw new InvalidDataException("asset");

    private static async Task<HttpResponseMessage> Get(string url, CancellationToken token)
    {
        Uri uri = new(url);
        for (int i = 0; i < 6; i++) {
            if (uri.Scheme != "https" || !uri.IsDefaultPort || uri.UserInfo != "" || uri.Host is not
                ("api.github.com" or "github.com" or "release-assets.githubusercontent.com" or "objects.githubusercontent.com" or "github-releases.githubusercontent.com"))
                throw new InvalidDataException("integrity");
            using var req = new HttpRequestMessage(HttpMethod.Get,uri);
            req.Headers.UserAgent.ParseAdd("BasisCharacter-Updater");
            var res = await Client.SendAsync(req,HttpCompletionOption.ResponseHeadersRead,token);
            if (res.StatusCode == HttpStatusCode.OK) return res;
            using (res) {
                if ((int)res.StatusCode is >=300 and <400 && res.Headers.Location is Uri next) { uri = new Uri(uri,next); continue; }
                throw new IOException((int)res.StatusCode switch { 404=>"missing", 403 or 429=>"rate", _=>"network" });
            }
        }
        throw new IOException("network");
    }
    private static async Task<string> Metadata(string suffix)
    {
        using var timer = new CancellationTokenSource(TimeSpan.FromSeconds(25));
        using var res = await Get(Api+suffix,timer.Token);
        await res.Content.LoadIntoBufferAsync(4*1024*1024);
        return await res.Content.ReadAsStringAsync(timer.Token);
    }
    internal static Task<string> Page(int n)
    {
        if (n < 1) throw new InvalidDataException("asset");
        return Metadata("?per_page=10&page="+n);
    }
    internal static async Task Prepare(string version)
    {
        if (Number(version) <= Number(Program.Version)) throw new InvalidDataException("asset");
        string tag = "basis-v"+version, name = "BasisCharacter-"+version+"-Windows-x64.zip";
        string url = "https://github.com/"+Repository+"/releases/download/"+tag+"/"+name;
        using var data = JsonDocument.Parse(await Metadata("/tags/"+tag)); var r = data.RootElement;
        if(r.GetProperty("tag_name").GetString()!=tag || r.GetProperty("draft").GetBoolean() || r.GetProperty("prerelease").GetBoolean()) throw new InvalidDataException("asset");
        var a = r.GetProperty("assets").EnumerateArray().Single(x=>x.GetProperty("name").GetString()==name);
        string digest = a.GetProperty("digest").GetString() ?? "";
        long size = a.GetProperty("size").GetInt64();
        if (a.GetProperty("browser_download_url").GetString()!=url || a.GetProperty("state").GetString()!="uploaded" ||
            !Regex.IsMatch(digest,@"^sha256:[a-f0-9]{64}$") || size<=0 || size>1200L*1024*1024) throw new InvalidDataException("asset");
        string cache = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"BasisCharacter","Updates");
        Directory.CreateDirectory(cache);
        foreach (string dir in Directory.EnumerateDirectories(cache)) {
            if (!Guid.TryParseExact(Path.GetFileName(dir),"N",out _) || File.GetAttributes(dir).HasFlag(FileAttributes.ReparsePoint) ||
                Directory.GetLastWriteTimeUtc(dir) > DateTime.UtcNow.AddDays(-1)) continue;
            try { Directory.Delete(dir,true); } catch (IOException) {} catch (UnauthorizedAccessException) {}
        }
        DirectoryInfo temp = Directory.CreateDirectory(Path.Combine(cache,Guid.NewGuid().ToString("N")));
        bool handedOff = false;
        try {
            string archive = Path.Combine(temp.FullName,"update.zip");
            using (var timeout = new CancellationTokenSource(TimeSpan.FromMinutes(20)))
            using (var response = await Get(url,timeout.Token))
            using (var input = await response.Content.ReadAsStreamAsync(timeout.Token))
            using (var output = File.Create(archive))
            using (var h = IncrementalHash.CreateHash(HashAlgorithmName.SHA256)) {
                byte[] buffer = new byte[131072]; int n; long total=0;
                while ((n=await input.ReadAsync(buffer,timeout.Token))>0) {
                    if ((total+=n)>size) throw new InvalidDataException("integrity");
                    h.AppendData(buffer,0,n); await output.WriteAsync(buffer.AsMemory(0,n),timeout.Token);
                }
                if(total!=size || "sha256:"+Convert.ToHexString(h.GetHashAndReset()).ToLowerInvariant()!=digest) throw new InvalidDataException("integrity");
            }
            await Task.Run(()=>ZipFile.ExtractToDirectory(archive,temp.FullName)); File.Delete(archive);
            string next = Path.Combine(temp.FullName,"BasisCharacter");
            if (!Directory.Exists(next) || !File.Exists(Path.Combine(next,Inventory)) || InstalledVersion(next)!=Number(version)) throw new InvalidDataException("integrity");
            string target = Path.TrimEndingDirectorySeparator(AppContext.BaseDirectory);
            // Prepare under the existing user's permissions before closing the running program.
            using (File.Create(Path.Combine(target,".basis-write-"+Guid.NewGuid()),1,FileOptions.DeleteOnClose)) {}
            string signal = "Local\\BasisUpdate-"+Guid.NewGuid();
            using var ready = new EventWaitHandle(false,EventResetMode.ManualReset,signal);
            var start = new ProcessStartInfo(Path.Combine(next,"BasisCharacter.exe")) { UseShellExecute=false };
            foreach(string value in new[]{"--apply-update",Environment.ProcessId.ToString(),target,signal}) start.ArgumentList.Add(value);
            using var helper = Process.Start(start) ?? throw new IOException("install");
            handedOff = await Task.Run(()=>ready.WaitOne(TimeSpan.FromSeconds(20)));
            if (!handedOff) throw new IOException("install");
        } finally { if (!handedOff) { try { temp.Delete(true); } catch (IOException) {} } }
    }
    private static Version InstalledVersion(string dir)
    {
        var v = AssemblyName.GetAssemblyName(Path.Combine(dir,"BasisCharacter.dll")).Version!;
        return new Version(v.Major,v.Minor,v.Build);
    }
    private static string Under(string root,string relative)
    {
        string[] parts = relative.Replace('\\','/').Split('/');
        if (parts.Any(s=>s.Length==0 || s=="." || s==".." || s.IndexOfAny(Path.GetInvalidFileNameChars())>=0)) throw new InvalidDataException("integrity");
        string result = root;
        foreach(string part in parts) {
            result=Path.Combine(result,part);
            if ((Directory.Exists(result)||File.Exists(result)) && File.GetAttributes(result).HasFlag(FileAttributes.ReparsePoint)) throw new InvalidDataException("location");
        }
        return result;
    }
    private static Dictionary<string,string> FilesIn(string dir) =>
        new(JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(Path.Combine(dir,Inventory)))!,StringComparer.OrdinalIgnoreCase);
    private static string Hash(string file) { using var s=File.OpenRead(file); return Convert.ToHexString(SHA256.HashData(s)).ToLowerInvariant(); }

    // A sibling temporary file and File.Replace keep each file intact. Backups are
    // retained until the new executable launches; unrelated user files are never enumerated for removal.
    internal static void Apply(string source,string target,Action launch)
    {
        var previous=FilesIn(target); var next=FilesIn(source);
        string work=Path.Combine(target,".basis-update-"+Guid.NewGuid()); Directory.CreateDirectory(work);
        var changes=new List<(string dest,string? backup)>();
        bool safeToClean=true;
        try {
            foreach(var (name,hash) in next) {
                string from=Under(source,name), to=Under(target,name);
                if(Hash(from)!=hash) throw new InvalidDataException("integrity");
                if(File.Exists(to) && !previous.ContainsKey(name)) throw new IOException("location");
            }
            void Put(string name) {
                string to=Under(target,name), from=Under(source,name);
                Directory.CreateDirectory(Path.GetDirectoryName(to)!);
                string staged=Path.Combine(work,"new-"+Guid.NewGuid()); File.Copy(from,staged);
                string? backup=null;
                if(File.Exists(to)) { backup=Path.Combine(work,Guid.NewGuid().ToString()); File.Replace(staged,to,backup); }
                else File.Move(staged,to);
                changes.Add((to,backup));
            }
            foreach(string name in next.Keys) {
                string to=Under(target,name);
                if(File.Exists(to) && previous.TryGetValue(name,out string? oldHash)) {
                    string installed=Hash(to);
                    if (installed==next[name] || (name.StartsWith("examples/",StringComparison.OrdinalIgnoreCase) && installed!=oldHash)) continue;
                }
                Put(name);
            }
            foreach(var (name,hash) in previous) if (!next.ContainsKey(name)) {
                string to=Under(target,name);
                if(!File.Exists(to) || Hash(to)!=hash) continue;
                string backup=Path.Combine(work,Guid.NewGuid().ToString()); File.Move(to,backup); changes.Add((to,backup));
            }
            Put(Inventory); launch();
        } catch {
            safeToClean=false;
            foreach(var change in changes.AsEnumerable().Reverse()) {
                if(change.backup==null) File.Delete(change.dest); else File.Move(change.backup,change.dest,true);
            }
            safeToClean=true; throw;
        } finally { if(safeToClean) { try { Directory.Delete(work,true); } catch(IOException) {} } }
    }
    internal static void CheckReplacement()
    {
        var tmp=Directory.CreateTempSubdirectory("BasisUpdateCheck-");
        try {
            string before=Path.Combine(tmp.FullName,"installed"), after=Path.Combine(tmp.FullName,"next");
            Directory.CreateDirectory(before); Directory.CreateDirectory(after);
            void Make(string dir, Dictionary<string,string> contents) {
                foreach(var (file,text) in contents) File.WriteAllText(Path.Combine(dir,file),text);
                var entries=contents.Keys.ToDictionary(n=>n,n=>Hash(Path.Combine(dir,n)));
                File.WriteAllText(Path.Combine(dir,Inventory),JsonSerializer.Serialize(entries));
            }
            Make(before,new(){{"application","old"},{"obsolete","old"}});
            Make(after,new(){{"application","new"},{"added","new"}});
            string project=Path.Combine(before,"project.json");
            File.WriteAllText(project,"user data");
            try { Apply(after,before,()=>throw new ApplicationException("test rollback")); }
            catch(ApplicationException) {}
            if(File.ReadAllText(Path.Combine(before,"application"))!="old" || !File.Exists(Path.Combine(before,"obsolete")) ||
                File.Exists(Path.Combine(before,"added"))) throw new IOException("Update rollback failed");
            Apply(after,before,()=>{});
            if(File.ReadAllText(Path.Combine(before,"application"))!="new" || File.Exists(Path.Combine(before,"obsolete")) ||
                !File.Exists(Path.Combine(before,"added")) || File.ReadAllText(project)!="user data") throw new IOException("Update replacement failed");
        } finally { tmp.Delete(true); }
    }
    internal static int Finish(string[] args)
    {
        try {
            if(args.Length!=4 || !int.TryParse(args[1],out int pid) || !args[3].StartsWith("Local\\BasisUpdate-",StringComparison.Ordinal)) return 1;
            using var parent=Process.GetProcessById(pid);
            string target=Path.GetFullPath(args[2]);
            if(!string.Equals(parent.MainModule?.FileName,Path.Combine(target,"BasisCharacter.exe"),StringComparison.OrdinalIgnoreCase) ||
                InstalledVersion(target)>=Number(Program.Version)) return 1;
            using var gate=new FileStream(Path.Combine(target,".basis-update.lock"),FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None,1,FileOptions.DeleteOnClose);
            using var ready=EventWaitHandle.OpenExisting(args[3]); ready.Set();
            if(!parent.WaitForExit(90000)) return 1;
            Apply(AppContext.BaseDirectory,target,()=>Process.Start(new ProcessStartInfo(Path.Combine(target,"BasisCharacter.exe")){UseShellExecute=false,WorkingDirectory=target}));
            return 0;
        } catch(Exception e) { MessageBox.Show(e.Message,"Basis Character",MessageBoxButtons.OK,MessageBoxIcon.Error); return 1; }
    }
}
