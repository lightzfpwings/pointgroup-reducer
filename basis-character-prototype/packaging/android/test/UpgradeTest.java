package io.github.lightzfpwings.basischaracter.test;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.ViewGroup;
import android.webkit.WebView;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import javax.net.ssl.HttpsURLConnection;
import java.security.cert.Certificate;
import org.json.*;

// This transport exists only in the instrumentation APK. The shipping app still
// calls its production GitHub endpoints and uses the real Android package installer.
public class UpgradeTest extends Instrumentation {
    private Bundle args;
    private WebView web;
    private volatile boolean corrupt=true;
    private static final String APP="io.github.lightzfpwings.basischaracter";
    public void onCreate(Bundle args) { super.onCreate(args); this.args=args; start(); }
    private String js(String script) throws Exception {
        CountDownLatch done=new CountDownLatch(1); AtomicReference<String> value=new AtomicReference<>();
        runOnMainSync(()->web.evaluateJavascript(script,v->{value.set(v);done.countDown();}));
        if(!done.await(5,TimeUnit.SECONDS)) throw new IOException("WebView timeout");
        return value.get();
    }
    private void until(String expression) throws Exception {
        long until=SystemClock.elapsedRealtime()+20000;
        while(SystemClock.elapsedRealtime()<until) { if("true".equals(js(expression))) return; SystemClock.sleep(160); }
        throw new IOException("Update UI did not reach "+expression+" / "+js("document.getElementById('update-status')?.textContent"));
    }
    private static final class Response extends HttpsURLConnection {
        final byte[] data;
        Response(URL url,byte[] data) { super(url); this.data=data; }
        public void connect() {} public void disconnect() {} public boolean usingProxy() { return false; }
        public String getCipherSuite(){return "fixture";} public Certificate[] getLocalCertificates(){return null;}
        public Certificate[] getServerCertificates(){return null;} public int getResponseCode(){return 200;}
        public InputStream getInputStream(){return new ByteArrayInputStream(data);}
    }
    public void onStart() {
        Bundle result=new Bundle(); int status=Activity.RESULT_CANCELED;
        try {
            if ("verify".equals(args.getString("phase"))) {
                if (!getTargetContext().getSharedPreferences("update-fixture",0).getBoolean("preserved",false))
                    throw new IOException("Upgrade lost application data");
                result.putString("result","BASIS_UPGRADE_PRESERVED");
            } else {
                String next=args.getString("version"), tag="basis-v"+next, name="BasisCharacter-"+next+"-Android.apk";
                String url="https://github.com/lightzfpwings/pointgroup-reducer/releases/download/"+tag+"/"+name;
                byte[] apk;
                try(InputStream in=getContext().getAssets().open("fixture.apk");ByteArrayOutputStream out=new ByteArrayOutputStream()){
                    byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);apk=out.toByteArray();
                }
                StringBuilder digest=new StringBuilder(); for(byte b:MessageDigest.getInstance("SHA-256").digest(apk))digest.append(String.format(Locale.ROOT,"%02x",b&255));
                JSONObject asset=new JSONObject().put("id",173).put("name",name).put("digest","sha256:"+digest).put("size",apk.length).put("state","uploaded").put("browser_download_url",url);
                JSONObject r=new JSONObject().put("tag_name",tag).put("draft",false).put("prerelease",false).put("assets",new JSONArray().put(asset));
                URL.setURLStreamHandlerFactory(protocol->{
                    if(!"https".equals(protocol))return null;
                    return new URLStreamHandler(){ protected URLConnection openConnection(URL u) throws IOException {
                        byte[] body;
                        if (u.toString().equals(url)) { body=apk.clone(); if(corrupt)body[0]^=1; }
                        else if (u.getPath().endsWith("/releases/tags/"+tag)) body=r.toString().getBytes(StandardCharsets.UTF_8);
                        else if(u.getPath().endsWith("/releases"))body=new JSONArray().put(r).toString().getBytes(StandardCharsets.UTF_8);
                        else throw new IOException("Unexpected update URL "+u.getHost());
                        return new Response(u,body);
                    }};
                });
                getTargetContext().getSharedPreferences("update-fixture",0).edit().putBoolean("preserved",true).commit();
                Intent i=getTargetContext().getPackageManager().getLaunchIntentForPackage(APP);
                Activity activity=startActivitySync(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
                runOnMainSync(()->web=(WebView)((ViewGroup)activity.findViewById(android.R.id.content)).getChildAt(0));
                until("window.BasisUpdatePlatform==='android' && !!document.getElementById('check-update').onclick");
                js("window.u=id=>document.getElementById(id);u('language').value='en';u('language').dispatchEvent(new Event('change'));u('check-update').click()");
                until("!u('install-update').hidden && u('update-status').textContent.includes('"+next+"')");
                js("u('install-update').click()"); until("u('update-status').textContent.includes('verification failed')");
                corrupt=false; js("u('install-update').click()");
                // The host accepts the OS installer prompt. A successful self-update
                // replaces this process, so verification continues in a fresh process.
                SystemClock.sleep(90000); throw new IOException("System installer did not replace the process");
            }
            status=Activity.RESULT_OK;
        } catch(Throwable e) { result.putString("error",android.util.Log.getStackTraceString(e)); }
        finish(status,result);
    }
}
