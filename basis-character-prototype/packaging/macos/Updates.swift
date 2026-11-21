import Cocoa
import CryptoKit

struct UpdateIssue: Error {
    let key: String
    init(_ key: String) { self.key = key }
}

private final class ReleaseRedirects: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        let allowed = ["api.github.com","github.com","release-assets.githubusercontent.com","objects.githubusercontent.com","github-releases.githubusercontent.com"]
        guard let u=request.url, u.scheme=="https", u.user==nil, u.password==nil, u.port==nil,
              allowed.contains(u.host ?? "") else { completionHandler(nil); return }
        completionHandler(request)
    }
}

enum MacUpdates {
    static let repo = "lightzfpwings/pointgroup-reducer"
    static let api = "https://api.github.com/repos/" + repo + "/releases"
    private static let session: URLSession = {
        let config = URLSessionConfiguration.ephemeral
        config.urlCache=nil; config.httpShouldSetCookies=false; config.timeoutIntervalForRequest=25; config.timeoutIntervalForResource=1200
        config.httpAdditionalHeaders=["User-Agent":"BasisCharacter-Updater"]
        return URLSession(configuration:config,delegate:ReleaseRedirects(),delegateQueue:nil)
    }()
    static func parts(_ version:String) throws -> [Int] {
        guard version.range(of:#"^(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})$"#,options:.regularExpression) != nil
        else { throw UpdateIssue("asset") }
        return version.split(separator:".").compactMap { Int($0) }
    }
    private static func check(_ response:URLResponse) throws {
        switch (response as? HTTPURLResponse)?.statusCode {
        case 200: return
        case 403,429: throw UpdateIssue("rate")
        case 404: throw UpdateIssue("missing")
        default: throw UpdateIssue("network")
        }
    }
    private static func metadata(_ suffix:String) async throws -> Data {
        let (data,response)=try await session.data(from:URL(string:api+suffix)!)
        try check(response)
        guard data.count<4*1024*1024 else { throw UpdateIssue("asset") }
        return data
    }
    static func page(_ n:Int) async throws -> String? {
        guard n>=1 else { throw UpdateIssue("asset") }
        return String(decoding:try await metadata("?per_page=10&page=\(n)"),as:UTF8.self)
    }
    static func download(_ version:String, current:String) async throws -> URL {
        guard try parts(current).lexicographicallyPrecedes(parts(version)) else { throw UpdateIssue("asset") }
        let tag="basis-v"+version, name="BasisCharacter-"+version+"-macOS-arm64.dmg"
        let address="https://github.com/"+repo+"/releases/download/"+tag+"/"+name
        let data=try await metadata("/tags/"+tag)
        guard let r=try JSONSerialization.jsonObject(with:data) as? [String:Any], r["tag_name"] as? String==tag,
              r["draft"] as? Bool==false, r["prerelease"] as? Bool==false,
              let assets=r["assets"] as? [[String:Any]], let a=assets.first(where:{$0["name"] as? String==name}),
              a["state"] as? String=="uploaded", a["browser_download_url"] as? String==address,
              let size=a["size"] as? Int, size>0, size<=256*1024*1024, let digest=a["digest"] as? String else { throw UpdateIssue("asset") }
        let (file,response)=try await session.download(from:URL(string:address)!)
        do {
            try check(response)
            guard try file.resourceValues(forKeys:[.fileSizeKey]).fileSize==size else { throw UpdateIssue("integrity") }
            let handle=try FileHandle(forReadingFrom:file); defer { try? handle.close() }
            var hash=SHA256()
            while let bytes=try handle.read(upToCount:131072), !bytes.isEmpty { hash.update(data:bytes) }
            guard "sha256:"+hash.finalize().map({String(format:"%02x",$0)}).joined()==digest else { throw UpdateIssue("integrity") }
            return file
        } catch { try? FileManager.default.removeItem(at:file); throw error }
    }
    @discardableResult
    static func run(_ path:String,_ args:[String]) throws -> String {
        let p=Process(), output=Pipe(); p.executableURL=URL(fileURLWithPath:path); p.arguments=args
        p.standardOutput=output; p.standardError=output
        try p.run(); let data=output.fileHandleForReading.readDataToEndOfFile(); p.waitUntilExit()
        guard p.terminationStatus==0 else { throw UpdateIssue("install") }
        return String(decoding:data,as:UTF8.self)
    }
    static func destination(_ current:URL) throws -> URL {
        let fm=FileManager.default
        if try current.resourceValues(forKeys:[.volumeIsReadOnlyKey]).volumeIsReadOnly != true && !current.path.contains("/AppTranslocation/") { return current }
        let user=fm.homeDirectoryForCurrentUser.appendingPathComponent("Applications",isDirectory:true)
        let local=user.appendingPathComponent("BasisCharacter.app"), shared=URL(fileURLWithPath:"/Applications/BasisCharacter.app")
        if fm.fileExists(atPath:local.path) { return local }
        if fm.fileExists(atPath:shared.path) { return shared }
        try fm.createDirectory(at:user,withIntermediateDirectories:true); return local
    }
    static func stagedApp(in image:URL, version:String, work:URL, identifier:String, current:URL) throws -> URL {
        let fm=FileManager.default, mount=work.appendingPathComponent("volume"), stage=work.appendingPathComponent("BasisCharacter.app")
        try fm.createDirectory(at:mount,withIntermediateDirectories:false)
        try run("/usr/bin/hdiutil",["attach","-readonly","-nobrowse","-noautoopen","-mountpoint",mount.path,image.path])
        defer { _ = try? run("/usr/bin/hdiutil",["detach",mount.path]) }
        let app=mount.appendingPathComponent("BasisCharacter.app")
        guard try app.resourceValues(forKeys:[.isSymbolicLinkKey]).isSymbolicLink==false,
              let bundle=Bundle(url:app), bundle.bundleIdentifier==identifier,
              bundle.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String==version else { throw UpdateIssue("integrity") }
        try run("/usr/bin/ditto",[app.path,stage.path])
        try run("/usr/bin/codesign",["--verify","--deep","--strict",stage.path])
        let team = try run("/usr/bin/codesign",["-dv","--verbose=4",current.path]).components(separatedBy:"\n").first{$0.hasPrefix("TeamIdentifier=")}
        if let team=team, team != "TeamIdentifier=not set" {
            guard try run("/usr/bin/codesign",["-dv","--verbose=4",stage.path]).components(separatedBy:"\n").contains(team) else { throw UpdateIssue("integrity") }
        }
        return stage
    }
    // On the same volume exchange the complete bundles atomically. The prior app
    // stays at the staging path until Launch Services confirms the relaunch.
    static func swap(_ a:URL,_ b:URL) throws {
        guard renameatx_np(AT_FDCWD,a.path,AT_FDCWD,b.path,UInt32(RENAME_SWAP))==0 else { throw UpdateIssue("location") }
    }
    @MainActor private static func authorizedManager() async throws -> FileManager {
        return try await withCheckedThrowingContinuation { continuation in
            NSWorkspace.shared.requestAuthorization(to:.replaceFile) { authorization, _ in
                guard let authorization=authorization else {
                    continuation.resume(throwing:UpdateIssue("location")); return
                }
                continuation.resume(returning:FileManager(authorization:authorization))
            }
        }
    }
    @MainActor static func reopen(_ target:URL) async throws {
        let config=NSWorkspace.OpenConfiguration(); config.createsNewApplicationInstance=true
        _ = try await NSWorkspace.shared.openApplication(at:target,configuration:config)
    }
    @MainActor static func install(_ image:URL, version:String, current:URL=Bundle.main.bundleURL,
                                   launch:@MainActor (URL) async throws -> Void = reopen) async throws {
        let fm=FileManager.default, target=try destination(current)
        guard let identifier=Bundle(url:current)?.bundleIdentifier else { throw UpdateIssue("integrity") }
        let exists=fm.fileExists(atPath:target.path)
        if exists {
            guard let b=Bundle(url:target), b.bundleIdentifier==identifier,
                  let old=b.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String,
                  try parts(old).lexicographicallyPrecedes(parts(version)) else { throw UpdateIssue("asset") }
        }
        let work=try fm.url(for:.itemReplacementDirectory,in:.userDomainMask,appropriateFor:target.deletingLastPathComponent(),create:true)
        var clean = true
        defer { if clean { try? fm.removeItem(at:work) } }
        let stage=try await Task.detached { try stagedApp(in:image,version:version,work:work,identifier:identifier,current:current) }.value
        var authorized:FileManager?
        let backup=work.appendingPathComponent("previous.app")
        if exists {
            do { try swap(target,stage) }
            catch {
                let manager=try await authorizedManager()
                try run("/usr/bin/ditto",[target.path,backup.path])
                _ = try manager.replaceItemAt(target,withItemAt:stage,backupItemName:nil,options:[])
                authorized=manager
            }
        } else { try fm.moveItem(at:stage,to:target) }
        do { try await launch(target) }
        catch {
            clean = false
            if let manager=authorized { _ = try manager.replaceItemAt(target,withItemAt:backup) }
            else if exists { try swap(target,stage) }
            else { try fm.moveItem(at:target,to:stage) }
            clean = true
            throw UpdateIssue("install")
        }
    }
}
