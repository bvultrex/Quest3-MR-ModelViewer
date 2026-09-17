# Quest Depth Browser

Experimental Meta Quest 3 / Quest 3S browser panel with **real-world Environment Depth occlusion**.

## v0.1 goal

A normal 2D Chromium-based Android `WebView` floats in passthrough MR as a spatial panel. The page itself does not use WebXR. Real objects such as a desk should be able to occlude the browser panel when the panel is positioned behind them.

## Architecture

- Meta Spatial SDK 0.14.0
- Android WebView (Chromium-based system WebView)
- Passthrough enabled
- `EnvironmentDepthMode.OCCLUSION`
- `UIPanelSettings` with `PanelRenderMode.Mesh()` for the first occlusion test
- Grabbable 1.45 m × 0.90 m panel
- Navigation: back, forward, reload, address bar, go
- Depth on/off toggle

The build pins Meta's official `Meta-Spatial-SDK-Samples` commit and patches the `MediaPlayerSample` in CI. This keeps the prototype small while inheriting Meta's known-good Spatial SDK project configuration.

## v0.1 test

1. Launch in a room with a table or desk.
2. Confirm passthrough is visible.
3. Confirm Wikipedia loads in the flat panel.
4. Grab the panel and place part of it behind the desk.
5. Verify the desk occludes the corresponding part of the panel.
6. Toggle `DEPTH OFF` and confirm the browser becomes visible through the desk again.

## Known trade-off

Mesh-rendered panels are less crisp than compositor layers. v0.1 prioritizes proving Environment Depth occlusion. If the test succeeds, the next experiment is layer rendering vs mesh rendering quality/occlusion.
