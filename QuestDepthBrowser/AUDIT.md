# Audit Log

## 2026-09-17 - v0.1 bootstrap

- Chose Meta Spatial SDK instead of a Chromium fork.
- Web content remains ordinary 2D Android WebView content.
- Pinned Meta Spatial SDK Samples commit `f233e2327b95f9871b75bdba867d6fdd726f07cc` (Spatial SDK 0.14.0 update).
- Chose `PanelRenderMode.Mesh()` for the first hardware test because the goal is real-world depth occlusion, not maximum text sharpness.
- Added explicit `DEPTH ON/OFF` control so hardware testing can compare occluded and non-occluded rendering without rebuilding.
- No WebXR requirement for page content.
