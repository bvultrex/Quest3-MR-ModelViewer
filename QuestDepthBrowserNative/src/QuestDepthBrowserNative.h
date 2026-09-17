#pragma once

#if defined(ANDROID)
#ifndef XR_USE_GRAPHICS_API_OPENGL_ES
#define XR_USE_GRAPHICS_API_OPENGL_ES 1
#endif
#ifndef XR_USE_PLATFORM_ANDROID
#define XR_USE_PLATFORM_ANDROID 1
#endif
#include <jni.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <GLES2/gl2ext.h>
#endif

#include <openxr/openxr.h>
#include <openxr/openxr_platform.h>

#include <array>
#include <vector>

class QuestDepthBrowserNative {
   public:
    QuestDepthBrowserNative() = default;
    ~QuestDepthBrowserNative() = default;

    bool Initialize(
        JNIEnv* env,
        jobject activity,
        XrSession session,
        uint32_t maxSwapchainWidth,
        uint32_t maxSwapchainHeight);

    void Render(
        JNIEnv* env,
        bool hasDepth,
        GLuint environmentDepthTexture,
        const float* depthViewLeft,
        const float* depthProjectionLeft,
        const float* depthViewRight,
        const float* depthProjectionRight);

    XrCompositionLayerQuad MakeLayer(int eye, XrSpace localSpace) const;
    bool IsReady() const { return Ready; }
    void Destroy(JNIEnv* env);

   private:
    bool CreateProgram();
    bool CreateSwapchains(XrSession session, uint32_t maxWidth, uint32_t maxHeight);
    bool CreateWebViewSurface(JNIEnv* env, jobject activity);
    bool RenderEye(
        int eye,
        bool hasDepth,
        GLuint environmentDepthTexture,
        const float* depthView,
        const float* depthProjection);
    void UpdateBrowserTexture(JNIEnv* env);

    GLuint CompileShader(GLenum type, const char* source);
    jclass LoadBridgeClass(JNIEnv* env, jobject activity);

    static constexpr float kPanelWidthMeters = 1.45f;
    static constexpr float kPanelHeightMeters = 0.90625f;
    static constexpr float kPanelCenterY = -0.02f;
    static constexpr float kPanelCenterZ = -1.15f;
    static constexpr int kRequestedWidth = 3200;
    static constexpr int kRequestedHeight = 2000;
    static constexpr int kDensityDpi = 320;

    bool Ready = false;
    XrSession Session = XR_NULL_HANDLE;
    int TextureWidth = 0;
    int TextureHeight = 0;

    GLuint ExternalTexture = 0;
    GLuint Program = 0;
    GLuint Framebuffer = 0;
    GLint BrowserTextureLocation = -1;
    GLint BrowserTextureTransformLocation = -1;
    GLint DepthTextureLocation = -1;
    GLint DepthViewLocation = -1;
    GLint DepthProjectionLocation = -1;
    GLint EyeLocation = -1;
    GLint HasDepthLocation = -1;

    jobject ActivityObject = nullptr;
    jobject SurfaceTextureObject = nullptr;
    jfloatArray SurfaceTransformArray = nullptr;
    jmethodID SurfaceUpdateTexImage = nullptr;
    jmethodID SurfaceGetTransformMatrix = nullptr;
    jmethodID SurfaceDetachFromGlContext = nullptr;
    std::array<float, 16> SurfaceTransform{};

    std::array<XrSwapchain, 2> Swapchains{{XR_NULL_HANDLE, XR_NULL_HANDLE}};
    std::array<std::vector<XrSwapchainImageOpenGLESKHR>, 2> SwapchainImages;
};
