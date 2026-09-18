package com.oculus.xrpassthroughocclusion;

import android.app.Activity;
import android.app.Presentation;
import android.content.Context;
import android.graphics.Color;
import android.graphics.SurfaceTexture;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.InputDevice;
import android.view.MotionEvent;
import android.view.Surface;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

public final class QuestBrowserPanelBridge {
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static VirtualDisplay virtualDisplay;
    private static BrowserPresentation presentation;
    private static Surface surface;
    private static WebView webView;
    private static int surfaceWidth;
    private static int surfaceHeight;

    private QuestBrowserPanelBridge() {}

    public static void start(
            final Activity activity,
            final SurfaceTexture surfaceTexture,
            final int width,
            final int height,
            final int densityDpi) {
        MAIN.post(() -> {
            stopInternal();
            try {
                surfaceWidth = width;
                surfaceHeight = height;
                surfaceTexture.setDefaultBufferSize(width, height);
                surface = new Surface(surfaceTexture);

                DisplayManager displayManager =
                        (DisplayManager) activity.getSystemService(Context.DISPLAY_SERVICE);
                int flags = DisplayManager.VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY |
                        DisplayManager.VIRTUAL_DISPLAY_FLAG_PRESENTATION;
                virtualDisplay = displayManager.createVirtualDisplay(
                        "QuestBrowserPanel",
                        width,
                        height,
                        densityDpi,
                        surface,
                        flags);
                if (virtualDisplay == null || virtualDisplay.getDisplay() == null) {
                    stopInternal();
                    return;
                }

                presentation = new BrowserPresentation(
                        activity,
                        virtualDisplay.getDisplay(),
                        width,
                        height);
                presentation.show();
            } catch (Throwable ignored) {
                stopInternal();
            }
        });
    }

    public static void pointer(final float normalizedX, final float normalizedY, final int action) {
        MAIN.post(() -> {
            if (webView == null) return;
            float nx = Math.max(0f, Math.min(1f, normalizedX));
            float ny = Math.max(0f, Math.min(1f, normalizedY));
            float width = webView.getWidth() > 0 ? webView.getWidth() : surfaceWidth;
            float height = webView.getHeight() > 0 ? webView.getHeight() : surfaceHeight;
            float x = nx * width;
            float y = ny * height;
            long now = SystemClock.uptimeMillis();
            try {
                if (action == MotionEvent.ACTION_HOVER_MOVE) {
                    MotionEvent hover = MotionEvent.obtain(
                            now, now, MotionEvent.ACTION_HOVER_MOVE, x, y, 0);
                    hover.setSource(InputDevice.SOURCE_MOUSE);
                    webView.dispatchGenericMotionEvent(hover);
                    hover.recycle();
                    return;
                }
                MotionEvent event = MotionEvent.obtain(now, now, action, x, y, 0);
                event.setSource(InputDevice.SOURCE_TOUCHSCREEN);
                webView.dispatchTouchEvent(event);
                event.recycle();
            } catch (Throwable ignored) {}
        });
    }

    public static void click(final float normalizedX, final float normalizedY) {
        MAIN.post(() -> {
            if (webView == null) return;
            float nx = Math.max(0f, Math.min(1f, normalizedX));
            float ny = Math.max(0f, Math.min(1f, normalizedY));
            float width = webView.getWidth() > 0 ? webView.getWidth() : surfaceWidth;
            float height = webView.getHeight() > 0 ? webView.getHeight() : surfaceHeight;
            float x = nx * width;
            float y = ny * height;
            long down = SystemClock.uptimeMillis();
            try {
                MotionEvent press = MotionEvent.obtain(
                        down, down, MotionEvent.ACTION_DOWN, x, y, 0);
                press.setSource(InputDevice.SOURCE_TOUCHSCREEN);
                webView.dispatchTouchEvent(press);
                press.recycle();
                MotionEvent release = MotionEvent.obtain(
                        down, SystemClock.uptimeMillis(), MotionEvent.ACTION_UP, x, y, 0);
                release.setSource(InputDevice.SOURCE_TOUCHSCREEN);
                webView.dispatchTouchEvent(release);
                release.recycle();
            } catch (Throwable ignored) {}
        });
    }

    public static void stop() {
        MAIN.post(QuestBrowserPanelBridge::stopInternal);
    }

    private static final class BrowserPresentation extends Presentation {
        private final int width;
        private final int height;

        BrowserPresentation(Context outerContext, android.view.Display display, int width, int height) {
            super(outerContext, display);
            this.width = width;
            this.height = height;
        }

        @Override
        protected void onCreate(Bundle savedInstanceState) {
            super.onCreate(savedInstanceState);
            requestWindowFeature(Window.FEATURE_NO_TITLE);

            FrameLayout root = new FrameLayout(getContext());
            root.setBackgroundColor(Color.rgb(18, 20, 24));

            webView = new WebView(getContext());
            webView.setBackgroundColor(Color.WHITE);
            webView.setFocusable(true);
            webView.setFocusableInTouchMode(true);
            webView.setLayerType(View.LAYER_TYPE_HARDWARE, null);

            WebSettings settings = webView.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setDomStorageEnabled(true);
            settings.setLoadWithOverviewMode(false);
            settings.setUseWideViewPort(true);
            settings.setBuiltInZoomControls(false);
            settings.setDisplayZoomControls(false);
            settings.setMediaPlaybackRequiresUserGesture(false);
            settings.setCacheMode(WebSettings.LOAD_DEFAULT);
            settings.setSupportZoom(true);

            webView.setWebViewClient(new WebViewClient());
            webView.setWebChromeClient(new WebChromeClient());
            root.addView(webView, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT));
            setContentView(root);

            Window window = getWindow();
            if (window != null) {
                window.setBackgroundDrawableResource(android.R.color.transparent);
                window.setLayout(width, height);
                WindowManager.LayoutParams attrs = window.getAttributes();
                attrs.width = width;
                attrs.height = height;
                attrs.gravity = Gravity.TOP | Gravity.LEFT;
                attrs.x = 0;
                attrs.y = 0;
                window.setAttributes(attrs);
                window.getDecorView().setPadding(0, 0, 0, 0);
                window.getDecorView().setSystemUiVisibility(
                        View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                        View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                        View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                        View.SYSTEM_UI_FLAG_FULLSCREEN |
                        View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
            }

            webView.loadUrl("https://www.wikipedia.org/");
        }
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
        surfaceWidth = 0;
        surfaceHeight = 0;
    }
}
