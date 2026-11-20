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
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
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
        String page = javascript("['status','xyz-feedback','review-state'].map(id=>document.getElementById(id).textContent)");
        throw new AssertionError("WebView condition failed: " + code + ", last=" + last + ", page=" + page);
    }

    private ActivityMonitor answerPicker(String action, Uri uri) {
        IntentFilter filter = new IntentFilter(action);
        filter.addCategory(Intent.CATEGORY_OPENABLE);
        try { filter.addDataType("*/*"); } catch (IntentFilter.MalformedMimeTypeException e) { throw new AssertionError(e); }
        return addMonitor(filter, new ActivityResult(Activity.RESULT_OK, new Intent().setData(uri)), true);
    }

    // A real scoped-storage content URI goes through the activity's normal
    // picker result handlers. Instrumentation supplies the user's document choices.
    private JSONObject readExport(ContentResolver resolver, Uri uri) throws Exception {
        for (int attempt = 0; attempt < 100; attempt++) {
            try (InputStream input = resolver.openInputStream(uri)) {
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                byte[] buffer = new byte[8192];
                int n;
                while ((n = input.read(buffer)) != -1) bytes.write(buffer, 0, n);
                return new JSONObject(bytes.toString("UTF-8"));
            } catch (java.io.FileNotFoundException | JSONException e) {
                // The document URI can be visible before the background export creates its file.
                SystemClock.sleep(100);
            }
        }
        throw new AssertionError("No completed JSON export");
    }

    @Override public void onStart() {
        Context target = getTargetContext();
        ContentResolver resolver = target.getContentResolver();
        Uri uri = null, xyz = null;
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
            javascript("window.byId=id=>document.getElementById(id);window.change=(id,v)=>{byId(id).value=v;byId(id).dispatchEvent(new Event('change'))};"
                + "change('workflow','vibrations');change('language','en');byId('formula-text').value='CH4';"
                + "byId('formula-text').dispatchEvent(new Event('input'));byId('find-models').click();byId('formula-choices').firstElementChild.click()");
            until("byId('group').value==='Td' && byId('calculate').disabled");
            javascript("byId('confirm-structure').click();byId('calculate').click()");
            until("byId('result-body').textContent.includes('IR allowed 2 · Raman allowed 4')");
            until("getComputedStyle(byId('result-body').querySelector('td')).textAlign==='center' && parseFloat(getComputedStyle(document.body).paddingTop)>=56 && parseFloat(getComputedStyle(document.body).paddingBottom)>=56");
            javascript("change('formula-catalog','C4H8')");
            until("byId('formula-choices').children.length===4 && byId('calculate').disabled");
            javascript("byId('formula-choices').children[1].click();byId('confirm-structure').click();byId('calculate').click()");
            until("byId('group').value==='C2h' && byId('result-body').textContent.includes('IR allowed 15 · Raman allowed 15')");
            javascript("change('formula-catalog','[Fe(CN)6]4-');byId('formula-choices').firstElementChild.click()");
            until("byId('group').value==='Oh' && byId('calculate').disabled && byId('model-origin').textContent.includes('Hexacyanoferrate(II)')");
            javascript("byId('confirm-structure').click();byId('calculate').click()");
            until("byId('result-body').textContent.includes('IR allowed 4 · Raman allowed 6')");

            values.clear();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, "Basis-water.xyz");
            values.put(MediaStore.MediaColumns.MIME_TYPE, "text/plain");
            xyz = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (xyz == null) throw new AssertionError("Missing XYZ test document");
            try (OutputStream out = resolver.openOutputStream(xyz)) {
                out.write("3\nwater\nO 0 0 0\nH 0.75695 0 0.58588\nH -0.75695 0 0.58588\n".getBytes(StandardCharsets.UTF_8));
            }
            ActivityMonitor xyzPicker = answerPicker(Intent.ACTION_OPEN_DOCUMENT, xyz);
            javascript("byId('open-xyz').click()");
            until("byId('composition').textContent==='H₂O' && byId('calculate').disabled");
            if (xyzPicker.getHits() != 1) throw new AssertionError("XYZ picker was not requested");
            removeMonitor(xyzPicker);
            javascript("change('group','C2v');byId('confirm-structure').click();byId('calculate').click()");
            until("byId('result-body').textContent.includes('IR allowed 3 · Raman allowed 3')");
            result.putString("result", "BASIS_SMOKE_OK");
            status = Activity.RESULT_OK;
        } catch (Throwable error) {
            result.putString("error", android.util.Log.getStackTraceString(error));
        } finally {
            if (uri != null) resolver.delete(uri, null, null);
            if (xyz != null) resolver.delete(xyz, null, null);
            if (activity != null) {
                final Activity active = activity;
                runOnMainSync(active::finish);
            }
            finish(status, result);
        }
    }
}
