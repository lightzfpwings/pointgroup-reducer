package io.github.lightzfpwings.basischaracter;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.WindowInsets;
import android.webkit.WebMessage;
import android.webkit.WebMessagePort;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final Uri ORIGIN = Uri.parse("https://appassets.androidplatform.net");
    private static final String PAGE = ORIGIN + "/index.html";
    private static final int OPEN = 1, SAVE = 2, STAGING = 3;
    private static final int MAX_INPUT = 2 * 1024 * 1024;
    private final ExecutorService files = Executors.newSingleThreadExecutor();
    private WebView web;
    private WebMessagePort channel;
    private boolean ready;
    private int picker;
    private String pendingImport;
    private File pendingExport;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        PackageInfo provider = WebView.getCurrentWebViewPackage();
        int major = 0;
        if (provider != null) {
            try { major = Integer.parseInt(provider.versionName.split("\\.")[0]); }
            catch (NumberFormatException ignored) { }
        }
        if (major < 109) {
            new AlertDialog.Builder(this).setMessage(R.string.update_webview)
                .setPositiveButton(android.R.string.ok, (dialog, which) -> finish())
                .setOnCancelListener(dialog -> finish()).show();
            return;
        }
        if (state != null) {
            picker = state.getInt("picker");
            String staged = state.getString("pendingExport");
            if (staged != null && staged.matches("export-[a-zA-Z0-9-]+\\.json")) {
                pendingExport = new File(getCacheDir(), staged);
            }
        }

        web = new WebView(this);
        setContentView(web);
        if (Build.VERSION.SDK_INT >= 35) {
            web.setOnApplyWindowInsetsListener((view, insets) -> {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars()
                    | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                return insets;
            });
        }
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setBlockNetworkLoads(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                // All work happens on the original document, including file selection.
                return true;
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (request.isForMainFrame() && PAGE.equals(request.getUrl().toString()) && "GET".equals(request.getMethod())) {
                    try {
                        return new WebResourceResponse("text/html", "UTF-8", 200, "OK",
                            Collections.singletonMap("Content-Security-Policy",
                                "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-src 'none'; base-uri 'none'; form-action 'none'"),
                            getAssets().open("index.html"));
                    } catch (IOException ignored) { }
                }
                return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found",
                    Collections.emptyMap(), new ByteArrayInputStream(new byte[0]));
            }
            @Override public void onPageFinished(WebView view, String url) {
                if (PAGE.equals(url) && PAGE.equals(view.getUrl())) connect();
            }
        });
        web.loadUrl(PAGE);
    }

    private void connect() {
        String bridge;
        try (InputStream input = getAssets().open("bridge.js")) {
            bridge = readText(input, 65536);
        } catch (IOException e) {
            toast(R.string.file_error);
            return;
        }
        web.evaluateJavascript(bridge, ignored -> {
            if (isDestroyed() || !PAGE.equals(web.getUrl())) return;
            if (channel != null) channel.close();
            ready = false;
            WebMessagePort[] ports = web.createWebMessageChannel();
            channel = ports[0];
            channel.setWebMessageCallback(new WebMessagePort.WebMessageCallback() {
                @Override public void onMessage(WebMessagePort port, WebMessage event) {
                    if (port != channel || !PAGE.equals(web.getUrl())) return;
                    try {
                        JSONObject message = new JSONObject(event.getData());
                        switch (message.getString("type")) {
                        case "ready": ready = true; deliverImport(); break;
                        case "openJSON": selectInput(); break;
                        case "saveJSON": stageExport(message.getJSONObject("payload")); break;
                        case "copyText": copy(message.getJSONObject("payload").getString("text")); break;
                        }
                    } catch (JSONException e) { toast(R.string.file_error); }
                }
            });
            web.postWebMessage(new WebMessage("basis-port", new WebMessagePort[]{ports[1]}), ORIGIN);
        });
    }

    private void selectInput() {
        if (picker != 0) return;
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
            .setType("*/*").putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"application/json", "text/plain", "application/octet-stream"});
        picker = OPEN;
        try { startActivityForResult(intent, OPEN); }
        catch (android.content.ActivityNotFoundException e) { picker = 0; toast(R.string.file_error); }
    }

    private void stageExport(JSONObject payload) throws JSONException {
        if (picker != 0) return;
        final String name = payload.getString("name"), text = payload.getString("text");
        if (!name.matches("[a-zA-Z0-9_.-]{1,155}\\.json") || text.length() > 128L * 1024 * 1024) {
            toast(R.string.file_error);
            return;
        }
        picker = STAGING;
        files.execute(() -> {
            File file = null;
            try {
                file = File.createTempFile("export-", ".json", getCacheDir());
                try (OutputStreamWriter writer = new OutputStreamWriter(new FileOutputStream(file), StandardCharsets.UTF_8)) {
                    writer.write(text);
                }
                if (file.length() > 128L * 1024 * 1024) throw new IOException();
                final File staged = file;
                runOnUiThread(() -> {
                    if (isDestroyed()) { staged.delete(); return; }
                    pendingExport = staged;
                    picker = SAVE;
                    Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                        .setType("application/json").putExtra(Intent.EXTRA_TITLE, name);
                    try { startActivityForResult(intent, SAVE); }
                    catch (android.content.ActivityNotFoundException e) {
                        staged.delete(); pendingExport = null; picker = 0; toast(R.string.file_error);
                    }
                });
            } catch (IOException e) {
                if (file != null) file.delete();
                runOnUiThread(() -> { picker = 0; toast(R.string.file_error); });
            }
        });
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != OPEN && request != SAVE) return;
        picker = 0;
        Uri uri = data == null ? null : data.getData();
        boolean selected = result == RESULT_OK && uri != null && "content".equals(uri.getScheme());
        if (request == SAVE) {
            final File staged = pendingExport;
            pendingExport = null;
            if (staged == null) return;
            if (!selected) { staged.delete(); return; }
            files.execute(() -> {
                try (InputStream input = new FileInputStream(staged);
                     OutputStream output = getContentResolver().openOutputStream(uri, "wt")) {
                    if (output == null) throw new IOException();
                    byte[] chunk = new byte[32768];
                    int count;
                    while ((count = input.read(chunk)) != -1) output.write(chunk, 0, count);
                } catch (IOException | SecurityException e) { toast(R.string.file_error); }
                finally { staged.delete(); }
            });
        } else if (selected) {
            files.execute(() -> {
                try (InputStream input = getContentResolver().openInputStream(uri)) {
                    if (input == null) throw new IOException();
                    String text = readText(input, MAX_INPUT);
                    runOnUiThread(() -> { pendingImport = text; deliverImport(); });
                } catch (LimitExceeded e) { toast(R.string.file_large); }
                catch (IOException | SecurityException e) { toast(R.string.file_error); }
            });
        }
    }

    private static final class LimitExceeded extends IOException {}
    private static String readText(InputStream input, int limit) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int count;
        while ((count = input.read(buffer)) != -1) {
            if (count > limit - bytes.size()) throw new LimitExceeded();
            bytes.write(buffer, 0, count);
        }
        return bytes.toString("UTF-8");
    }

    private void deliverImport() {
        if (ready && !isDestroyed() && pendingImport != null && PAGE.equals(web.getUrl())) {
            channel.postMessage(new WebMessage(pendingImport));
            pendingImport = null;
        }
    }

    private void copy(String text) {
        try {
            getSystemService(ClipboardManager.class).setPrimaryClip(ClipData.newPlainText("Basis Character", text));
        } catch (RuntimeException e) { toast(R.string.clipboard_error); }
    }

    private void toast(int resource) {
        runOnUiThread(() -> { if (!isDestroyed()) Toast.makeText(this, resource, Toast.LENGTH_LONG).show(); });
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        state.putInt("picker", picker == STAGING ? 0 : picker);
        if (pendingExport != null) state.putString("pendingExport", pendingExport.getName());
    }

    @Override protected void onDestroy() {
        ready = false;
        if (channel != null) channel.close();
        files.shutdown();
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
