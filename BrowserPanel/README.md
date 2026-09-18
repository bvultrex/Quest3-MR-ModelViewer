# BrowserPanel experiment v0.1

Base: Quest3 MR Model Viewer v1.0.1 hardware-accepted final.

This experiment adds one spatial browser object to the proven Viewer renderer. It intentionally does not reuse the old browser compositor/depth pipeline.

## v0.1 scope

- Android WebView / Chromium loads Wikipedia
- WebView -> VirtualDisplay -> SurfaceTexture -> GL_TEXTURE_EXTERNAL_OES
- browser texture is drawn inside the existing Viewer multiview projection pass
- BrowserMode changes only the material source; Environment Depth stays on the Viewer's proven 3x3 soft-occlusion shader path
- both controllers can ray-hit the browser panel
- trigger forwards a click to WebView
- grip near the panel moves and rotates it with preserved hand offset

Not included yet: resize handles, URL bar, tabs, downloads, favorites, system keyboard integration, DE-QWERTZ remap.

## Hardware acceptance checkpoint

1. Wikipedia is fully visible with no right-edge crop.
2. Text is sharp enough to read comfortably.
3. Trigger opens a link.
4. Grip moves and rotates the panel.
5. A real table/desk occludes the panel with the same soft edge quality as GLB models.

Do not add resize/browser chrome until this checkpoint is confirmed on Quest 3 hardware.
