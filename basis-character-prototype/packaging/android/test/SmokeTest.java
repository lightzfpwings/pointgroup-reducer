package io.github.lightzfpwings.basischaracter.test;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.ClipboardManager;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemClock;
import android.provider.MediaStore;
import android.view.ViewGroup;
import android.webkit.WebView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

public final class SmokeTest extends Instrumentation {
    private WebView web;
    private static final String APP = "io.github.lightzfpwings.basischaracter";

    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        start();
    }

    private String javascript(String code) throws Exception {
        CountDownLatch result = new CountDownLatch(1);
        AtomicReference<String> value = new AtomicReference<>();
        runOnMainSync(() -> web.evaluateJavascript(code, text -> { value.set(text); result.countDown(); }));
        if (!result.await(5, TimeUnit.SECONDS)) throw new AssertionError("No JavaScript response");
        return value.get();
    }

    private void until(String code) throws Exception {
        String last = "";
        for (int i = 0; i < 100; i++) {
            last = javascript(code);
            if ("true".equals(last)) return;
            SystemClock.sleep(150);
        }
        throw new AssertionError("WebView condition failed: " + code + ", last=" + last);
    }

    private ActivityMonitor answerPicker(String action, Uri uri) {
        IntentFilter filter = new IntentFilter(action);
        filter.addCategory(Intent.CATEGORY_OPENABLE);
        try { filter.addDataType("*/*"); } catch (IntentFilter.MalformedMimeTypeException e) { throw new AssertionError(e); }
        return addMonitor(filter, new ActivityResult(Activity.RESULT_OK, new Intent().setData(uri)), true);
    }

    // A real scoped-storage content URI goes through the activity's normal
    // picker result handlers. Only the user's two picker choices are automated.
    private JSONObject readExport(ContentResolver resolver, Uri uri) throws Exception {
        for (int attempt = 0; attempt < 100; attempt++) {
            try (InputStream input = resolver.openInputStream(uri)) {
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                byte[] buffer = new byte[8192];
                int n;
                while ((n = input.read(buffer)) != -1) bytes.write(buffer, 0, n);
                return new JSONObject(bytes.toString("UTF-8"));
            } catch (org.json.JSONException e) { SystemClock.sleep(100); }
        }
        throw new AssertionError("No completed JSON export");
    }

    @Override public void onStart() {
        Context target = getTargetContext();
        ContentResolver resolver = target.getContentResolver();
        Uri uri = null;
        Activity activity = null;
        Bundle result = new Bundle();
        int status = Activity.RESULT_CANCELED;
        try {
            activity = startActivitySync(new Intent(Intent.ACTION_MAIN).setClassName(APP, APP + ".MainActivity")
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            final Activity active = activity;
            runOnMainSync(() -> web = (WebView) ((ViewGroup)active.findViewById(android.R.id.content)).getChildAt(0));
            until("!!(window.BasisDesktop && window.webkit && window.webkit.messageHandlers.saveJSON)");
            javascript("document.querySelector('[data-template=water]').click();document.getElementById('calculate').click()");
            until("!document.getElementById('export-result').disabled");
            javascript("document.getElementById('calculate-salc').click()");
            until("document.getElementById('salc-irrep').options.length === 2");
            javascript("document.getElementById('copy-text').click()");
            ClipboardManager clipboard = target.getSystemService(ClipboardManager.class);
            boolean copied = false;
            for (int i = 0; i < 30; i++) {
                android.content.ClipData clip = clipboard.getPrimaryClip();
                if (clip != null && clip.getItemAt(0).coerceToText(target).toString().contains("SALC")) { copied = true; break; }
                SystemClock.sleep(150);
            }
            if (!copied) throw new AssertionError("Native clipboard lost the SALC table");

            ContentValues values = new ContentValues();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, "Basis-instrumentation.json");
            values.put(MediaStore.MediaColumns.MIME_TYPE, "application/json");
            uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) throw new AssertionError("Missing test document URI");
            ActivityMonitor save = answerPicker(Intent.ACTION_CREATE_DOCUMENT, uri);
            javascript("document.getElementById('export-result').click()");
            JSONObject exported = readExport(resolver, uri);
            if (save.getHits() != 1) throw new AssertionError("Save picker was not requested");
            removeMonitor(save);
            JSONArray spaces = exported.getJSONObject("salc").getJSONArray("spaces");
            for (int i = 0; i < 2; i++) {
                JSONObject space = spaces.getJSONObject(i);
                JSONArray c = space.getJSONArray("copies").getJSONObject(0).getJSONArray("vectors").getJSONObject(0).getJSONArray("coefficients");
                if (!(i == 0 ? "A1" : "B1").equals(space.getString("irrep"))
                    || Math.abs(c.getDouble(0) * c.getDouble(1) - (i == 0 ? .5 : -.5)) > 1e-7) {
                    throw new AssertionError("Wrong water SALCs: " + spaces);
                }
            }
            javascript("document.getElementById('new-project').click()");
            ActivityMonitor open = answerPicker(Intent.ACTION_OPEN_DOCUMENT, uri);
            javascript("document.getElementById('load-project').click()");
            until("document.getElementById('group').value === 'C2v' && document.getElementById('function-count').textContent.trim().startsWith('2')");
            if (open.getHits() != 1) throw new AssertionError("Open picker was not requested");
            removeMonitor(open);
            result.putString("result", "BASIS_SMOKE_OK");
            status = Activity.RESULT_OK;
        } catch (Throwable error) {
            result.putString("error", android.util.Log.getStackTraceString(error));
        } finally {
            if (uri != null) resolver.delete(uri, null, null);
            if (activity != null) {
                final Activity active = activity;
                runOnMainSync(active::finish);
            }
            finish(status, result);
        }
    }
}
