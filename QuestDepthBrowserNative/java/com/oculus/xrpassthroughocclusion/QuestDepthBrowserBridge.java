package com.oculus.xrpassthroughocclusion;

import android.app.Activity;
import android.app.Presentation;
import android.content.Context;
import android.graphics.Color;
import android.graphics.SurfaceTexture;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.Surface;
import android.view.ViewGroup;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class QuestDepthBrowserBridge {
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static VirtualDisplay virtualDisplay;
    private static Presentation presentation;
    private static Surface surface;
    private static WebView webView;
    private static EditText addressBar;

    private QuestDepthBrowserBridge() {}

    public static void start(
            final Activity activity,
            final SurfaceTexture surfaceTexture,
            final int width,
            final int height,
            final int densityDpi) {
        MAIN.post(() -> {
            stopInternal();
            try {
                surface = new Surface(surfaceTexture);
                DisplayManager displayManager =
                        (DisplayManager) activity.getSystemService(Context.DISPLAY_SERVICE);
                int flags = DisplayManager.VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY |
                        DisplayManager.VIRTUAL_DISPLAY_FLAG_PRESENTATION;
                virtualDisplay = displayManager.createVirtualDisplay(
                        "QuestDepthBrowserNative",
                        width,
                        height,
                        densityDpi,
                        surface,
                        flags);
                if (virtualDisplay == null || virtualDisplay.getDisplay() == null) {
                    stopInternal();
                    return;
                }

                presentation = new Presentation(activity, virtualDisplay.getDisplay());
                presentation.setContentView(createBrowserUi(activity));
                presentation.show();
                webView.loadUrl("https://www.wikipedia.org/");
            } catch (Throwable ignored) {
                stopInternal();
            }
        });
    }

    public static void stop() {
        MAIN.post(QuestDepthBrowserBridge::stopInternal);
    }

    private static ViewGroup createBrowserUi(Activity activity) {
        final float density = activity.getResources().getDisplayMetrics().density;
        LinearLayout root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(12, 17, 22));

        LinearLayout toolbar = new LinearLayout(activity);
        toolbar.setOrientation(LinearLayout.HORIZONTAL);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(dp(8, density), dp(6, density), dp(8, density), dp(6, density));
        toolbar.setBackgroundColor(Color.rgb(45, 61, 78));

        Button back = button(activity, "◀");
        Button forward = button(activity, "▶");
        Button reload = button(activity, "↻");
        Button go = button(activity, "GO");
        TextView badge = new TextView(activity);
        badge.setText(" NATIVE DEPTH v0.2.0 ");
        badge.setTextColor(Color.WHITE);
        badge.setTextSize(15f);
        badge.setGravity(Gravity.CENTER);
        badge.setBackgroundColor(Color.rgb(27, 122, 78));

        addressBar = new EditText(activity);
        addressBar.setSingleLine(true);
        addressBar.setText("https://www.wikipedia.org/");
        addressBar.setTextColor(Color.WHITE);
        addressBar.setHintTextColor(Color.LTGRAY);
        addressBar.setTextSize(17f);
        addressBar.setBackgroundColor(Color.rgb(68, 91, 115));
        addressBar.setPadding(dp(14, density), 0, dp(14, density), 0);

        toolbar.addView(back, fixed(dp(70, density), dp(54, density)));
        toolbar.addView(forward, fixed(dp(70, density), dp(54, density)));
        toolbar.addView(reload, fixed(dp(70, density), dp(54, density)));
        toolbar.addView(addressBar, new LinearLayout.LayoutParams(
                0, dp(54, density), 1f));
        toolbar.addView(go, fixed(dp(74, density), dp(54, density)));
        toolbar.addView(badge, fixed(dp(210, density), dp(54, density)));

        webView = new WebView(activity);
        webView.setBackgroundColor(Color.rgb(12, 17, 22));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                if (addressBar != null) addressBar.setText(url);
            }
        });
        webView.setWebChromeClient(new WebChromeClient());

        back.setOnClickListener(v -> {
            if (webView != null && webView.canGoBack()) webView.goBack();
        });
        forward.setOnClickListener(v -> {
            if (webView != null && webView.canGoForward()) webView.goForward();
        });
        reload.setOnClickListener(v -> {
            if (webView != null) webView.reload();
        });
        go.setOnClickListener(v -> navigate());
        addressBar.setOnEditorActionListener((v, actionId, event) -> {
            navigate();
            return true;
        });

        root.addView(toolbar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(68, density)));
        root.addView(webView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        return root;
    }

    private static Button button(Activity activity, String text) {
        Button button = new Button(activity);
        button.setText(text);
        button.setTextSize(16f);
        button.setAllCaps(false);
        button.setTextColor(Color.rgb(25, 30, 35));
        return button;
    }

    private static LinearLayout.LayoutParams fixed(int width, int height) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(width, height);
        params.setMargins(2, 0, 2, 0);
        return params;
    }

    private static int dp(int value, float density) {
        return Math.max(1, Math.round(value * density));
    }

    private static void navigate() {
        if (webView == null || addressBar == null) return;
        String url = addressBar.getText().toString().trim();
        if (url.isEmpty()) return;
        if (!url.contains("://")) url = "https://" + url;
        webView.loadUrl(url);
    }

    private static void stopInternal() {
        try {
            if (webView != null) {
                webView.stopLoading();
                webView.loadUrl("about:blank");
                webView.destroy();
            }
        } catch (Throwable ignored) {}
        webView = null;
        addressBar = null;

        try {
            if (presentation != null) presentation.dismiss();
        } catch (Throwable ignored) {}
        presentation = null;

        try {
            if (virtualDisplay != null) virtualDisplay.release();
        } catch (Throwable ignored) {}
        virtualDisplay = null;

        try {
            if (surface != null) surface.release();
        } catch (Throwable ignored) {}
        surface = null;
    }
}
