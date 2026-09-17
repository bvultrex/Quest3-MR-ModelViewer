from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
SRC = ROOT / 'Src'
JAVA_DIR = ROOT / 'java/com/oculus/xrpassthroughocclusion'
ANDROID = ROOT / 'Projects/Android'
JAVA = JAVA_DIR / 'QuestDepthBrowserBridge.java'
CPP = SRC / 'QuestDepthBrowserNative.cpp'
HEADER = SRC / 'QuestDepthBrowserNative.h'

def rep(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing {label}')
    return text.replace(old,new,1)


# Version bump to v0.2.3.
gradle_path = ANDROID / 'build.gradle'
gradle = gradle_path.read_text()
gradle = rep(gradle, 'versionCode 22', 'versionCode 23', 'Gradle versionCode')
gradle = rep(gradle, 'versionName "0.2.2"', 'versionName "0.2.3"', 'Gradle versionName')
gradle_path.write_text(gradle)

manifest_path = ANDROID / 'AndroidManifest.xml'
manifest = manifest_path.read_text()
manifest = rep(manifest, 'android:versionCode="22"', 'android:versionCode="23"', 'manifest versionCode')
manifest = rep(manifest, 'android:versionName="0.2.2"', 'android:versionName="0.2.3"', 'manifest versionName')
manifest_path.write_text(manifest)

# Return to a comfortable Quest-browser-like default width. Height is set independently
# to 16:9 below and is no longer coupled to the 3200x2000 backing texture.
h = HEADER.read_text()
h = rep(h, 'static constexpr float kInitialPanelWidthMeters = 1.00f;', 'static constexpr float kInitialPanelWidthMeters = 1.20f;', 'initial panel width')
HEADER.write_text(h)

# Java
j=JAVA.read_text()
j=rep(j,'import android.graphics.drawable.ColorDrawable;\n','import android.graphics.drawable.ColorDrawable;\nimport android.graphics.drawable.GradientDrawable;\n','gradient import')
j=rep(j,'    private static FrameLayout rootFrame;\n    private static PointerOverlay pointerOverlay;\n',
'''    private static FrameLayout rootFrame;\n    private static FrameLayout contentFrame;\n    private static LinearLayout browserRoot;\n    private static LinearLayout toolbar;\n    private static Button expandToolbarButton;\n    private static PointerOverlay pointerOverlay;\n    private static boolean toolbarCollapsed;\n''','java fields')

# insert setWindowAspect before stop
anchor='''    public static void stop() {\n        MAIN.post(QuestDepthBrowserBridge::stopInternal);\n    }\n'''
method=r'''    public static void setWindowAspect(final float requestedAspect) {
        MAIN.post(() -> {
            if (contentFrame == null || surfaceWidth <= 0 || surfaceHeight <= 0) return;
            float aspect = Math.max(0.55f, Math.min(3.20f, requestedAspect));
            float textureAspect = (float) surfaceWidth / (float) surfaceHeight;
            int width;
            int height;
            if (aspect >= textureAspect) {
                width = surfaceWidth;
                height = Math.max(1, Math.round(surfaceWidth / aspect));
            } else {
                height = surfaceHeight;
                width = Math.max(1, Math.round(surfaceHeight * aspect));
            }
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(width, height, Gravity.CENTER);
            contentFrame.setLayoutParams(params);
            contentFrame.requestLayout();
            contentFrame.invalidate();
        });
    }

''' + anchor
j=rep(j,anchor,method,'setWindowAspect method')

# replace pointer method body root target references
j=j.replace('if (rootFrame == null) return;','if (contentFrame == null) return;',1)
j=j.replace('float width = rootFrame.getWidth() > 0 ? rootFrame.getWidth() : surfaceWidth;\n            float height = rootFrame.getHeight() > 0 ? rootFrame.getHeight() : surfaceHeight;',
'''float width = contentFrame.getWidth() > 0 ? contentFrame.getWidth() : surfaceWidth;
            float height = contentFrame.getHeight() > 0 ? contentFrame.getHeight() : surfaceHeight;''',1)
j=j.replace('rootFrame.dispatchGenericMotionEvent(hover);','contentFrame.dispatchGenericMotionEvent(hover);',1)
j=j.replace('rootFrame.dispatchTouchEvent(touch);','contentFrame.dispatchTouchEvent(touch);',1)

# replace createBrowserUi entirely
start=j.index('    private static ViewGroup createBrowserUi(Context context) {')
end=j.index('    private static View currentInputTarget()', start)
new_ui=r'''    private static ViewGroup createBrowserUi(Context context) {
        final float density = context.getResources().getDisplayMetrics().density;

        rootFrame = new FrameLayout(context);
        rootFrame.setBackgroundColor(Color.TRANSPARENT);

        contentFrame = new FrameLayout(context);
        contentFrame.setBackgroundColor(Color.rgb(24, 25, 27));

        browserRoot = new LinearLayout(context);
        browserRoot.setOrientation(LinearLayout.VERTICAL);
        browserRoot.setBackgroundColor(Color.rgb(24, 25, 27));

        toolbar = new LinearLayout(context);
        toolbar.setOrientation(LinearLayout.HORIZONTAL);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(dp(10, density), dp(7, density), dp(10, density), dp(7, density));
        toolbar.setBackgroundColor(Color.rgb(32, 33, 36));

        Button back = button(context, "‹");
        Button forward = button(context, "›");
        Button reload = button(context, "↻");
        Button go = button(context, "GO");
        Button collapse = button(context, "^");
        collapse.setContentDescription("Adressleiste einklappen");

        addressBar = new EditText(context);
        addressBar.setSingleLine(true);
        addressBar.setText("https://www.wikipedia.org/");
        addressBar.setSelectAllOnFocus(true);
        addressBar.setTextColor(Color.WHITE);
        addressBar.setHintTextColor(Color.rgb(180, 182, 186));
        addressBar.setTextSize(16f);
        addressBar.setBackground(roundedBackground(Color.rgb(55, 56, 60), dp(18, density)));
        addressBar.setPadding(dp(18, density), 0, dp(18, density), 0);

        toolbar.addView(back, fixed(dp(58, density), dp(50, density)));
        toolbar.addView(forward, fixed(dp(58, density), dp(50, density)));
        toolbar.addView(reload, fixed(dp(58, density), dp(50, density)));
        toolbar.addView(addressBar, new LinearLayout.LayoutParams(0, dp(50, density), 1f));
        toolbar.addView(go, fixed(dp(66, density), dp(50, density)));
        toolbar.addView(collapse, fixed(dp(52, density), dp(50, density)));

        webView = new WebView(context);
        webView.setBackgroundColor(Color.rgb(24, 25, 27));
        webView.setFocusable(true);
        webView.setFocusableInTouchMode(true);
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
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                if (addressBar != null && !addressBar.hasFocus()) addressBar.setText(url);
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

        expandToolbarButton = button(context, "⌄");
        expandToolbarButton.setContentDescription("Adressleiste ausklappen");
        expandToolbarButton.setVisibility(View.GONE);
        FrameLayout.LayoutParams expandParams = new FrameLayout.LayoutParams(
                dp(72, density), dp(38, density), Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        expandParams.topMargin = dp(4, density);

        collapse.setOnClickListener(v -> setToolbarCollapsed(true));
        expandToolbarButton.setOnClickListener(v -> setToolbarCollapsed(false));

        browserRoot.addView(toolbar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(64, density)));
        browserRoot.addView(webView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        contentFrame.addView(browserRoot, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
        contentFrame.addView(expandToolbarButton, expandParams);
        pointerOverlay = new PointerOverlay(context);
        contentFrame.addView(pointerOverlay, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        rootFrame.addView(contentFrame, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT,
                Gravity.CENTER));
        toolbarCollapsed = false;
        return rootFrame;
    }

    private static void setToolbarCollapsed(boolean collapsed) {
        toolbarCollapsed = collapsed;
        if (toolbar != null) toolbar.setVisibility(collapsed ? View.GONE : View.VISIBLE);
        if (expandToolbarButton != null) {
            expandToolbarButton.setVisibility(collapsed ? View.VISIBLE : View.GONE);
        }
        if (browserRoot != null) browserRoot.requestLayout();
    }

'''
j=j[:start]+new_ui+j[end:]

# button style + rounded helper
old='''    private static Button button(Context context, String text) {\n        Button button = new Button(context);\n        button.setText(text);\n        button.setTextSize(16f);\n        button.setAllCaps(false);\n        button.setTextColor(Color.rgb(25, 30, 35));\n        return button;\n    }\n'''
new=r'''    private static Button button(Context context, String text) {
        Button button = new Button(context);
        button.setText(text);
        button.setTextSize(17f);
        button.setAllCaps(false);
        button.setTextColor(Color.WHITE);
        button.setBackground(roundedBackground(Color.rgb(47, 48, 52), dp(15, context.getResources().getDisplayMetrics().density)));
        button.setPadding(0, 0, 0, 0);
        return button;
    }

    private static GradientDrawable roundedBackground(int color, int radiusPx) {
        GradientDrawable background = new GradientDrawable();
        background.setColor(color);
        background.setCornerRadius(radiusPx);
        return background;
    }
'''
j=rep(j,old,new,'button helper')

# cleanup fields
j=rep(j,'        rootFrame = null;\n        pointerOverlay = null;\n',
'''        rootFrame = null;
        contentFrame = null;
        browserRoot = null;
        toolbar = null;
        expandToolbarButton = null;
        toolbarCollapsed = false;
        pointerOverlay = null;
''','cleanup fields')

# Pointer overlay add handle paint and corner drawing
j=rep(j,'        private final Paint dot = new Paint(Paint.ANTI_ALIAS_FLAG);\n',
'''        private final Paint dot = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint handle = new Paint(Paint.ANTI_ALIAS_FLAG);
''','handle paint field')
j=rep(j,'            dot.setColor(Color.rgb(54, 156, 255));\n',
'''            dot.setColor(Color.rgb(54, 156, 255));
            handle.setStyle(Paint.Style.STROKE);
            handle.setStrokeWidth(6f);
            handle.setStrokeCap(Paint.Cap.ROUND);
            handle.setColor(Color.argb(185, 232, 233, 236));
''','handle paint setup')
old_draw='''        @Override\n        protected void onDraw(Canvas canvas) {\n            super.onDraw(canvas);\n            if (!visible) return;\n            canvas.drawCircle(x, y, 15f, ring);\n            canvas.drawCircle(x, y, 5f, dot);\n        }\n'''
new_draw=r'''        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            final float inset = 13f;
            final float len = 32f;
            final float w = getWidth();
            final float h = getHeight();
            // Native-Quest-style resize affordances: four subtle grabbable corners.
            canvas.drawLine(inset, inset, inset + len, inset, handle);
            canvas.drawLine(inset, inset, inset, inset + len, handle);
            canvas.drawLine(w - inset, inset, w - inset - len, inset, handle);
            canvas.drawLine(w - inset, inset, w - inset, inset + len, handle);
            canvas.drawLine(inset, h - inset, inset + len, h - inset, handle);
            canvas.drawLine(inset, h - inset, inset, h - inset - len, handle);
            canvas.drawLine(w - inset, h - inset, w - inset - len, h - inset, handle);
            canvas.drawLine(w - inset, h - inset, w - inset, h - inset - len, handle);
            if (!visible) return;
            canvas.drawCircle(x, y, 15f, ring);
            canvas.drawCircle(x, y, 5f, dot);
        }
'''
j=rep(j,old_draw,new_draw,'pointer draw')
j=j.replace('DEPTH v0.2.2','DEPTH v0.2.3')
JAVA.write_text(j)

# C++
c=CPP.read_text()
# add content rect uniform
c=rep(c,'uniform mat4 uBrowserTextureTransform;\n','uniform mat4 uBrowserTextureTransform;\nuniform vec4 uBrowserContentRect;\n','shader content uniform')
c=rep(c,'    vec4 transformedUv = uBrowserTextureTransform * vec4(vUv, 0.0, 1.0);\n',
'''    vec2 sourceUv = uBrowserContentRect.xy + vUv * uBrowserContentRect.zw;
    vec4 transformedUv = uBrowserTextureTransform * vec4(sourceUv, 0.0, 1.0);
''','shader source uv')
# globals before CheckXr
c=rep(c,'bool CheckXr(const char* label, XrResult result) {\n',
'''GLint gBrowserContentRectLocation = -1;
jmethodID gSetWindowAspectMethod = nullptr;
float gLastWindowAspect = -1.0f;

bool CheckXr(const char* label, XrResult result) {
''','native globals')
# program uniform location
c=rep(c,'    BrowserTextureTransformLocation = glGetUniformLocation(Program, "uBrowserTextureTransform");\n',
'''    BrowserTextureTransformLocation = glGetUniformLocation(Program, "uBrowserTextureTransform");
    gBrowserContentRectLocation = glGetUniformLocation(Program, "uBrowserContentRect");
''','content rect location')
# method lookup and initial aspect method; after HidePointer method
c=rep(c,'    HidePointerMethod = env->GetStaticMethodID(BridgeClass, "hidePointer", "()V");\n    if (PointerMethod == nullptr || HidePointerMethod == nullptr) {\n',
'''    HidePointerMethod = env->GetStaticMethodID(BridgeClass, "hidePointer", "()V");
    gSetWindowAspectMethod = env->GetStaticMethodID(BridgeClass, "setWindowAspect", "(F)V");
    if (PointerMethod == nullptr || HidePointerMethod == nullptr || gSetWindowAspectMethod == nullptr) {
''','aspect method lookup')
# after CallStatic start before delete refs: call aspect
start_call='''    env->CallStaticVoidMethod(\n        bridgeClass,\n        startMethod,\n        activity,\n        SurfaceTextureObject,\n        TextureWidth,\n        TextureHeight,\n        kDensityDpi);\n'''
start_repl=start_call+'''    const float initialAspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);
    env->CallStaticVoidMethod(BridgeClass, gSetWindowAspectMethod, initialAspect);
    gLastWindowAspect = initialAspect;
'''
c=rep(c,start_call,start_repl,'initial aspect sync')
# initial height 16:9
c=rep(c,'    PanelHeightMeters = PanelWidthMeters *\n        (static_cast<float>(TextureHeight) / static_cast<float>(TextureWidth));\n',
'''    // Quest-browser-like default shape. The WebView viewport is dynamically fitted
    // inside the fixed high-resolution backing texture, so it no longer dictates aspect.
    PanelHeightMeters = PanelWidthMeters * (9.0f / 16.0f);
''','initial panel 16:9')
# RenderEye content rect uniform after BrowserTransform uniform
uniform_anchor='''    glUniformMatrix4fv(\n        BrowserTextureTransformLocation,\n        1,\n        GL_FALSE,\n        SurfaceTransform.data());\n'''
uniform_repl=uniform_anchor+r'''    const float panelAspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);
    const float textureAspect = static_cast<float>(TextureWidth) /
        std::max(static_cast<float>(TextureHeight), 1.0f);
    float contentOffsetX = 0.0f;
    float contentOffsetY = 0.0f;
    float contentScaleX = 1.0f;
    float contentScaleY = 1.0f;
    if (panelAspect >= textureAspect) {
        contentScaleY = textureAspect / panelAspect;
        contentOffsetY = (1.0f - contentScaleY) * 0.5f;
    } else {
        contentScaleX = panelAspect / textureAspect;
        contentOffsetX = (1.0f - contentScaleX) * 0.5f;
    }
    glUniform4f(
        gBrowserContentRectLocation,
        contentOffsetX,
        contentOffsetY,
        contentScaleX,
        contentScaleY);
'''
c=rep(c,uniform_anchor,uniform_repl,'content rect uniform upload')

# replace entire HandleInput
s=c.index('void QuestDepthBrowserNative::HandleInput(')
e=c.index('\nvoid QuestDepthBrowserNative::Render(',s)
new_handle=r'''void QuestDepthBrowserNative::HandleInput(
    JNIEnv* env,
    const XrPosef& aimPose,
    bool aimActive,
    bool triggerPressed,
    float gripValue,
    float thumbstickY) {
    (void)thumbstickY;
    if (!Ready || BridgeClass == nullptr) return;

    const bool gripPressed = aimActive && gripValue > 0.55f;
    if (!aimActive) {
        if (HidePointerMethod != nullptr) {
            env->CallStaticVoidMethod(BridgeClass, HidePointerMethod);
            if (env->ExceptionCheck()) env->ExceptionClear();
        }
        TriggerWasPressed = triggerPressed;
        GripWasPressed = gripPressed;
        PointerWasInside = false;
        return;
    }

    const XrVector3f forward = RotateVectorByQuaternion(
        aimPose.orientation, XrVector3f{0.0f, 0.0f, -1.0f});

    bool rayHitsPlane = false;
    bool inside = false;
    float hitX = PanelCenter.x;
    float hitY = PanelCenter.y;
    float u = LastPointerU;
    float v = LastPointerV;
    if (std::abs(forward.z) > 0.00001f) {
        const float t = (PanelCenter.z - aimPose.position.z) / forward.z;
        if (t > 0.0f) {
            rayHitsPlane = true;
            hitX = aimPose.position.x + forward.x * t;
            hitY = aimPose.position.y + forward.y * t;
            u = (hitX - PanelCenter.x) / PanelWidthMeters + 0.5f;
            v = (hitY - PanelCenter.y) / PanelHeightMeters + 0.5f;
            inside = u >= 0.0f && u <= 1.0f && v >= 0.0f && v <= 1.0f;
        }
    }

    // Corner order: 0 LB, 1 RB, 2 LT, 3 RT. Grabbing the panel body moves it;
    // grabbing a corner resizes width and height independently while the opposite
    // corner stays fixed, matching normal spatial-window behavior.
    static int resizeCorner = -1;
    static XrVector3f fixedCorner{0.0f, 0.0f, 0.0f};
    const float cornerZone = 0.115f;
    int hoveredCorner = -1;
    if (inside) {
        const bool left = u <= cornerZone;
        const bool right = u >= 1.0f - cornerZone;
        const bool bottom = v <= cornerZone;
        const bool top = v >= 1.0f - cornerZone;
        if (left && bottom) hoveredCorner = 0;
        else if (right && bottom) hoveredCorner = 1;
        else if (left && top) hoveredCorner = 2;
        else if (right && top) hoveredCorner = 3;
    }

    auto syncWindowAspect = [&]() {
        if (gSetWindowAspectMethod == nullptr) return;
        const float aspect = PanelWidthMeters / std::max(PanelHeightMeters, 0.001f);
        if (std::abs(aspect - gLastWindowAspect) < 0.0025f) return;
        env->CallStaticVoidMethod(BridgeClass, gSetWindowAspectMethod, aspect);
        if (env->ExceptionCheck()) env->ExceptionClear();
        gLastWindowAspect = aspect;
    };

    if (gripPressed) {
        if (!GripWasPressed) {
            if (hoveredCorner >= 0 && rayHitsPlane) {
                resizeCorner = hoveredCorner;
                const bool movingRight = resizeCorner == 1 || resizeCorner == 3;
                const bool movingTop = resizeCorner == 2 || resizeCorner == 3;
                const float sx = movingRight ? 1.0f : -1.0f;
                const float sy = movingTop ? 1.0f : -1.0f;
                fixedCorner = {
                    PanelCenter.x - sx * PanelWidthMeters * 0.5f,
                    PanelCenter.y - sy * PanelHeightMeters * 0.5f,
                    PanelCenter.z};
            } else {
                resizeCorner = -1;
                GrabDistance = std::max(
                    0.45f,
                    std::min(3.0f, Distance3(PanelCenter, aimPose.position)));
            }
        }

        if (resizeCorner >= 0 && rayHitsPlane) {
            const bool movingRight = resizeCorner == 1 || resizeCorner == 3;
            const bool movingTop = resizeCorner == 2 || resizeCorner == 3;
            const float sx = movingRight ? 1.0f : -1.0f;
            const float sy = movingTop ? 1.0f : -1.0f;
            const float requestedWidth = (hitX - fixedCorner.x) * sx;
            const float requestedHeight = (hitY - fixedCorner.y) * sy;
            const float newWidth = std::max(0.48f, std::min(2.60f, requestedWidth));
            const float newHeight = std::max(0.30f, std::min(1.80f, requestedHeight));
            const float movingX = fixedCorner.x + sx * newWidth;
            const float movingY = fixedCorner.y + sy * newHeight;
            PanelWidthMeters = newWidth;
            PanelHeightMeters = newHeight;
            PanelCenter.x = (fixedCorner.x + movingX) * 0.5f;
            PanelCenter.y = (fixedCorner.y + movingY) * 0.5f;
            syncWindowAspect();
        } else {
            PanelCenter = {
                aimPose.position.x + forward.x * GrabDistance,
                aimPose.position.y + forward.y * GrabDistance,
                aimPose.position.z + forward.z * GrabDistance};
        }

        if (HidePointerMethod != nullptr) {
            env->CallStaticVoidMethod(BridgeClass, HidePointerMethod);
            if (env->ExceptionCheck()) env->ExceptionClear();
        }
        PointerWasInside = false;
        TriggerWasPressed = triggerPressed;
        GripWasPressed = true;
        return;
    }
    resizeCorner = -1;

    if (inside && PointerMethod != nullptr) {
        LastPointerU = u;
        LastPointerV = v;
        int action = 7; // MotionEvent.ACTION_HOVER_MOVE
        if (triggerPressed && !TriggerWasPressed) action = 0; // DOWN
        else if (!triggerPressed && TriggerWasPressed) action = 1; // UP
        else if (triggerPressed) action = 2; // MOVE while pressed
        env->CallStaticVoidMethod(BridgeClass, PointerMethod, u, v, action);
        if (env->ExceptionCheck()) env->ExceptionClear();
        PointerWasInside = true;
    } else {
        if (!triggerPressed && TriggerWasPressed && PointerWasInside && PointerMethod != nullptr) {
            env->CallStaticVoidMethod(
                BridgeClass,
                PointerMethod,
                LastPointerU,
                LastPointerV,
                1);
            if (env->ExceptionCheck()) env->ExceptionClear();
        }
        if (HidePointerMethod != nullptr) {
            env->CallStaticVoidMethod(BridgeClass, HidePointerMethod);
            if (env->ExceptionCheck()) env->ExceptionClear();
        }
        PointerWasInside = false;
    }

    TriggerWasPressed = triggerPressed;
    GripWasPressed = false;
}
'''
c=c[:s]+new_handle+c[e:]
# cleanup global method
c=rep(c,'    PointerMethod = nullptr;\n    HidePointerMethod = nullptr;\n',
'''    PointerMethod = nullptr;
    HidePointerMethod = nullptr;
    gSetWindowAspectMethod = nullptr;
    gLastWindowAspect = -1.0f;
''','native cleanup globals')
CPP.write_text(c)

print('Quest Depth Browser Native v0.2.3 patch applied')
print('Spatial window: independent corner resize + opposite-corner anchor')
print('Browser viewport: dynamic aspect/reflow inside fixed 3200x2000 backing texture')
print('UI: sticky Quest-style URL bar with ^ collapse control')
print('Rendering core: compositor-sharp per-eye quads + Environment Depth preserved')
