package com.eink.shell;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.ViewGroup;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Minimal WebView shell: one editable Host address, one WebView, no bundled web assets.
 *
 * <p>The address is saved in SharedPreferences. A first launch (or a launch with the
 * {@code url} string extra) opens the address dialog or that address directly, so
 * {@code adb shell am start -n com.eink.shell/.MainActivity -e url http://host:8000/manage}
 * can provision the shell during acceptance.
 */
public final class MainActivity extends Activity {
    private static final String PREFS = "eink-shell";
    private static final String KEY_URL = "host_url";
    private static final String DEFAULT_HINT = "http://<电脑IP>:8000/manage";

    private SharedPreferences prefs;
    private WebView webView;
    private TextView addressLabel;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.WHITE);

        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(10), dp(6), dp(10), dp(6));

        addressLabel = new TextView(this);
        addressLabel.setTextSize(12);
        addressLabel.setTextColor(Color.BLACK);
        addressLabel.setSingleLine(true);
        bar.addView(addressLabel, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button address = new Button(this);
        address.setText("地址");
        address.setOnClickListener(view -> showAddressDialog());
        bar.addView(address);

        Button reload = new Button(this);
        reload.setText("重载");
        reload.setOnClickListener(view -> webView.reload());
        bar.addView(reload);

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        webView.setWebViewClient(new WebViewClient());
        webView.setBackgroundColor(Color.WHITE);

        root.addView(bar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(webView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        setContentView(root);

        String intentUrl = getIntent().getStringExtra("url");
        if (intentUrl != null && !intentUrl.trim().isEmpty()) {
            open(intentUrl);
            return;
        }
        String saved = prefs.getString(KEY_URL, "");
        if (saved.isEmpty()) {
            showAddressDialog();
        } else {
            open(saved);
        }
    }

    private void showAddressDialog() {
        EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        input.setSingleLine(true);
        input.setHint(DEFAULT_HINT);
        input.setText(prefs.getString(KEY_URL, ""));
        new AlertDialog.Builder(this)
                .setTitle("Host 地址")
                .setView(input)
                .setPositiveButton("打开", (dialog, which) -> open(input.getText().toString()))
                .setNegativeButton("取消", null)
                .show();
    }

    private void open(String value) {
        String url = normalize(value);
        if (url == null) {
            new AlertDialog.Builder(this)
                    .setMessage("地址要以 http:// 或 https:// 开头，并包含主机名")
                    .setPositiveButton("知道了", null)
                    .show();
            return;
        }
        prefs.edit().putString(KEY_URL, url).apply();
        addressLabel.setText(url);
        webView.loadUrl(url);
    }

    static String normalize(String value) {
        String url = value == null ? "" : value.trim();
        if (url.isEmpty()) {
            return null;
        }
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "http://" + url;
        }
        Uri parsed = Uri.parse(url);
        if (parsed.getHost() == null || parsed.getHost().isEmpty()) {
            return null;
        }
        return url;
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
