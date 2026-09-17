# Project State

Current target: **v0.2.0 Native Depth Compositor proof**

Hardware evidence from v0.1.x:

- Spatial SDK `Mesh()` gives working Environment Depth but visibly soft browser text.
- Spatial SDK `Layer()` gives sharp browser text but bypasses Environment Depth.
- Hole-punch experiment did not restore Environment Depth for the compositor layer.
- 150% eye-buffer scale and sharper mesh sampling did not close the quality gap.

v0.2.0 therefore bypasses the Spatial SDK panel renderer entirely.

Implementation baseline:

- Meta OpenXR SDK v85 `XrPassthroughOcclusion`
- `XR_META_environment_depth`
- Android `WebView`
- `VirtualDisplay -> Surface -> SurfaceTexture`
- GLES `samplerExternalOES`
- two eye-specific RGBA OpenXR swapchains
- two `XrCompositionLayerQuad` submissions
- 3x3 depth-edge soft mask based on the proven model-viewer occlusion pass

Next checkpoint: APK builds, launches, shows Wikipedia sharply, and a real desk/table occludes the quad correctly in both eyes.
