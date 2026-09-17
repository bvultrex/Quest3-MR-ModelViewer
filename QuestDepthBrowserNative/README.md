# Quest Depth Browser Native v0.2.0

Native OpenXR proof-of-concept for Meta Quest 3 / Quest 3S.

Goal: combine the sharpness of OpenXR compositor quad layers with real-world `XR_META_environment_depth` occlusion.

## Pipeline

1. Android Chromium `WebView` renders to a 3200x2000 virtual display.
2. The virtual display targets a detached `SurfaceTexture`.
3. Native GLES attaches the `SurfaceTexture` as `GL_TEXTURE_EXTERNAL_OES`.
4. For each eye, the browser image is rendered into its own OpenXR swapchain.
5. The fragment shader projects each browser pixel into the corresponding Environment Depth view and writes a soft alpha mask.
6. Two `XrCompositionLayerQuad` layers are submitted, one `LEFT`, one `RIGHT`.
7. Passthrough remains the backmost compositor layer.

The regular projection layer is intentionally not submitted in v0.2.0. This prevents the browser texture from being resampled through the eye buffer.

## v0.2.0 hardware-test scope

- fixed 1.45 m x 0.90625 m browser panel
- panel center at roughly 1.15 m in front of local origin
- Wikipedia start page
- sharp compositor rendering
- per-eye Environment Depth alpha masking
- no XR pointer/touch forwarding yet

This is a render-path proof. Interaction, grabbing, resizing, tabs and full browser controls come after sharpness + depth are proven together.
