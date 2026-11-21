package io.github.lightzfpwings.basischaracter;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.*;
import java.net.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.ExecutorService;
import javax.net.ssl.HttpsURLConnection;

final class AppUpdate {
    static final String VERSION = "(0|[1-9][0-9]{0,5})\\.(0|[1-9][0-9]{0,2})\\.(0|[1-9][0-9]{0,2})";
    static final String REPO = "lightzfpwings/pointgroup-reducer";
    private static final String API = "https://api.github.com/repos/" + REPO + "/releases";
    private static final int PERMISSION = 701, INSTALL = 702;
    private final MainActivity activity;
    private final ExecutorService io;
    private String waiting;
    private int installId;
    private int externalRequest;
    private String pendingFile;
    AppUpdate(MainActivity activity, ExecutorService io, Bundle state) {
        this.activity = activity; this.io = io;
        if (state != null) { waiting = state.getString("updateVersion"); installId = state.getInt("updateID"); externalRequest=state.getInt("updateRequest"); pendingFile=state.getString("updateFile"); }
    }
    void save(Bundle state) {
        if (externalRequest != 0) {
            state.putString("updateVersion",waiting); state.putInt("updateID",installId);
            state.putInt("updateRequest",externalRequest); state.putString("updateFile",pendingFile);
        }
    }
    static long versionCode(String version) throws IOException {
        if (version == null || !version.matches(VERSION)) throw new IOException("asset");
        String[] part = version.split("\\.");
        return Long.parseLong(part[0])*1000000 + Integer.parseInt(part[1])*1000L + Integer.parseInt(part[2]);
    }
    private static long code(PackageInfo p) { return Build.VERSION.SDK_INT >= 28 ? p.getLongVersionCode() : p.versionCode; }
    private static int flags() { return Build.VERSION.SDK_INT >= 28 ? PackageManager.GET_SIGNING_CERTIFICATES : PackageManager.GET_SIGNATURES; }
    private static Set<Signature> signers(PackageInfo p) {
        Signature[] s = Build.VERSION.SDK_INT >= 28 ? p.signingInfo.getApkContentsSigners() : p.signatures;
        return new HashSet<>(Arrays.asList(s));
    }
    static String hex(byte[] data) {
        StringBuilder s = new StringBuilder(); for (byte b:data) s.append(String.format(Locale.ROOT,"%02x",b & 255)); return s.toString();
    }
    private static HttpsURLConnection open(String address) throws IOException {
        URL url = new URL(address);
        for (int n=0;n<6;n++) {
            String h=url.getHost();
            if (!"https".equals(url.getProtocol()) || url.getUserInfo()!=null || url.getPort()!=-1 ||
                !Arrays.asList("api.github.com","github.com","release-assets.githubusercontent.com","objects.githubusercontent.com","github-releases.githubusercontent.com").contains(h)) throw new IOException("integrity");
            HttpsURLConnection c=(HttpsURLConnection)url.openConnection();
            c.setInstanceFollowRedirects(false); c.setConnectTimeout(12000); c.setReadTimeout(25000);
            c.setRequestProperty("User-Agent","BasisCharacter-Updater"); c.setUseCaches(false);
            int status=c.getResponseCode();
            if (status==200) return c;
            String next=c.getHeaderField("Location"); c.disconnect();
            if (status>=300 && status<400 && next!=null) { url=new URL(url,next); continue; }
            throw new IOException(status==404 ? "missing" : status==403 || status==429 ? "rate" : "network");
        }
        throw new IOException("network");
    }
    private static String metadata(String suffix) throws IOException {
        HttpsURLConnection c=open(API+suffix);
        try (InputStream in=c.getInputStream(); ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] buf=new byte[8192]; int n;
            while ((n=in.read(buf))!=-1) { if (out.size()+n>4*1024*1024) throw new IOException("asset"); out.write(buf,0,n); }
            return out.toString("UTF-8");
        } finally { c.disconnect(); }
    }
    private static String page(int number) throws Exception {
        // A release body can be much larger than a WebView IPC message. Only
        // these fields and the Android asset are needed by the shared resolver.
        JSONArray releases=new JSONArray(metadata("?per_page=10&page="+number));
        JSONArray rows=new JSONArray();
        for (int i=0;i<releases.length();i++) {
            JSONObject release=releases.getJSONObject(i), row=new JSONObject();
            for(String key:new String[]{"tag_name","draft","prerelease"}) row.put(key,release.get(key));
            JSONArray files=new JSONArray(), assets=release.getJSONArray("assets");
            for(int j=0;j<assets.length();j++) {
                JSONObject a=assets.getJSONObject(j);
                if(!a.getString("name").endsWith("-Android.apk")) continue;
                JSONObject copy=new JSONObject();
                for(String key:new String[]{"id","name","size","state","digest","browser_download_url"}) copy.put(key,a.opt(key));
                files.put(copy);
            }
            rows.put(row.put("assets",files));
        }
        return rows.toString();
    }
    private void reply(int id,String status,String text) {
        activity.runOnUiThread(()->activity.updateReply(id,status,text));
    }
    private static String error(Exception e) {
        String m=e.getMessage();
        return Arrays.asList("asset","integrity","rate","permission","location","install").contains(m) ? m : "network";
    }
    void handle(JSONObject request) throws Exception {
        int id=request.getInt("id");
        if ("page".equals(request.getString("action"))) {
            int page=request.getInt("page"); if(page<1) { reply(id,"asset",null); return; }
            io.execute(()->{try { reply(id,"ok",page(page)); }
                catch(Exception e) { reply(id,error(e),null); }});
        } else if ("install".equals(request.getString("action"))) {
            if(installId!=0) { reply(id,"busy",null); return; }
            String v=request.getString("version");
            if (versionCode(v)<=code(activity.getPackageManager().getPackageInfo(activity.getPackageName(),0))) { reply(id,"asset",null); return; }
            installId=id; waiting=v;
            if(activity.getPackageManager().canRequestPackageInstalls()) download();
            else try {
                externalRequest=PERMISSION;
                activity.startActivityForResult(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,Uri.parse("package:"+activity.getPackageName())),PERMISSION);
            } catch(RuntimeException e) { finish("permission"); }
        }
    }
    boolean result(int request,int result) {
        if(request==PERMISSION) {
            externalRequest=0;
            if(waiting!=null && activity.getPackageManager().canRequestPackageInstalls()) download(); else finish("permission");
        } else if(request==INSTALL) finish(result==Activity.RESULT_OK?"ok":"cancelled"); else return false;
        return true;
    }
    private void finish(String status) {
        if (pendingFile!=null && pendingFile.matches("release-[0-9-]+\\.apk"))
            new File(new File(activity.getCacheDir(),"updates"),pendingFile).delete();
        int id=installId; waiting=null; pendingFile=null; installId=0; externalRequest=0;
        reply(id,status,null);
    }
    private void download() {
        final String v=waiting;
        io.execute(()->{
            try {
                String tag="basis-v"+v, name="BasisCharacter-"+v+"-Android.apk";
                JSONObject release=new JSONObject(metadata("/tags/"+tag));
                if (!tag.equals(release.getString("tag_name")) || release.getBoolean("draft") || release.getBoolean("prerelease")) throw new IOException("asset");
                JSONArray assets=release.getJSONArray("assets"); JSONObject asset=null;
                for(int i=0;i<assets.length();i++) if (name.equals(assets.getJSONObject(i).getString("name"))) asset=assets.getJSONObject(i);
                String url="https://github.com/"+REPO+"/releases/download/"+tag+"/"+name;
                if(asset==null || !"uploaded".equals(asset.optString("state")) || !url.equals(asset.optString("browser_download_url"))) throw new IOException("asset");
                long size=asset.getLong("size"); String digest=asset.getString("digest");
                if (size<=0 || size>128L*1024*1024 || !digest.matches("sha256:[a-f0-9]{64}")) throw new IOException("asset");
                File dir=new File(activity.getCacheDir(),"updates"); if (!dir.isDirectory() && !dir.mkdirs()) throw new IOException("install");
                File[] old=dir.listFiles();
                if(old!=null) for(File item:old) if(item.getName().matches("release-[0-9-]+\\.apk") && item.lastModified()<System.currentTimeMillis()-86400000L) item.delete();
                File file=File.createTempFile("release-", ".apk",dir);
                try {
                    HttpsURLConnection c=open(url); MessageDigest hash=MessageDigest.getInstance("SHA-256");
                    try (InputStream in=c.getInputStream(); OutputStream out=new FileOutputStream(file)) {
                        byte[] buf=new byte[32768]; int n; long total=0;
                        while((n=in.read(buf))!=-1) { total+=n; if(total>size) throw new IOException("integrity"); hash.update(buf,0,n); out.write(buf,0,n); }
                        if(total!=size || !digest.equals("sha256:"+hex(hash.digest()))) throw new IOException("integrity");
                    } finally { c.disconnect(); }
                    verifyPackage(file,v);
                    activity.runOnUiThread(()->{
                        if(activity.isDestroyed()) { file.delete(); return; }
                        Uri uri=Uri.parse("content://"+activity.getPackageName()+".updates/"+file.getName());
                        Intent intent=new Intent(Intent.ACTION_INSTALL_PACKAGE,uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                        intent.setClipData(ClipData.newRawUri("APK",uri)); intent.putExtra(Intent.EXTRA_RETURN_RESULT,true);
                        try { pendingFile=file.getName(); externalRequest=INSTALL; activity.startActivityForResult(intent,INSTALL); }
                        catch(RuntimeException e) { file.delete(); finish("install"); }
                    });
                } catch(Exception e) { file.delete(); throw e; }
            } catch(Exception e) { activity.runOnUiThread(()->finish(error(e))); }
        });
    }
    void verifyPackage(File apk,String version) throws Exception {
        PackageManager pm=activity.getPackageManager();
        PackageInfo installed=pm.getPackageInfo(activity.getPackageName(),flags()), next=pm.getPackageArchiveInfo(apk.toString(),flags());
        if (next==null || !installed.packageName.equals(next.packageName) || !version.equals(next.versionName) ||
            versionCode(version)!=code(next) || code(next)<=code(installed) || signers(installed).isEmpty() || !signers(installed).equals(signers(next))) throw new IOException("integrity");
    }
}
