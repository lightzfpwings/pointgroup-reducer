// Compile with Updates.swift. Both successful replacement and a failed relaunch
// use a disposable copy of the old app, never a user's installed application.
import Foundation

@main struct UpdateTest {
    @MainActor static func main() async throws {
        let args=CommandLine.arguments
        guard args.count==4 else { throw UpdateIssue("usage: test-update old.app new.dmg new-version") }
        let fm=FileManager.default, work=fm.temporaryDirectory.appendingPathComponent("BasisReplaceTest-"+UUID().uuidString)
        try fm.createDirectory(at:work,withIntermediateDirectories:false)
        defer { try? fm.removeItem(at:work) }
        let target=work.appendingPathComponent("BasisCharacter.app"), image=URL(fileURLWithPath:args[2]), version=args[3]
        try MacUpdates.run("/usr/bin/ditto",[args[1],target.path])
        let marker=work.appendingPathComponent("my-project.json")
        try Data("user project".utf8).write(to:marker)
        func installed(_ app:URL) throws -> String {
            let data=try Data(contentsOf:app.appendingPathComponent("Contents/Info.plist"))
            let p=try PropertyListSerialization.propertyList(from:data,format:nil) as? [String:Any]
            return p?["CFBundleShortVersionString"] as? String ?? ""
        }
        let old=try installed(target)
        do {
            try await MacUpdates.install(image,version:version,current:target) { app in
                guard try installed(app)==version else { throw UpdateIssue("wrong staged version") }
                throw UpdateIssue("test relaunch failure")
            }
            throw UpdateIssue("rollback was not exercised")
        } catch let e as UpdateIssue where e.key=="install" {}
        guard try installed(target)==old else { throw UpdateIssue("rollback failed") }
        try await MacUpdates.install(image,version:version,current:target) { app in
            let report=try MacUpdates.run(app.appendingPathComponent("Contents/MacOS/BasisCharacter").path,["--self-check"])
            let result=try JSONSerialization.jsonObject(with:Data(report.utf8)) as? [String:Any]
            guard result?["status"] as? String=="passed", result?["version"] as? String==version else { throw UpdateIssue("relaunch failed") }
        }
        guard try installed(target)==version, try String(contentsOf:marker)=="user project" else { throw UpdateIssue("replacement failed") }
        print("Verified DMG replacement, rollback, application restart and project preservation: "+old+" -> "+version)
    }
}
