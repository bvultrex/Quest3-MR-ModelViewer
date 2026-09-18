# BrowserPanel v0.1 hardware checkpoint

Status: HARDWARE ACCEPTED on Meta Quest 3.

Confirmed before starting v0.2:
- Wikipedia renders completely, including the right edge.
- Browser image/text is sharp.
- Existing Viewer Environment Depth occlusion works on the browser panel.
- Controller ray + trigger opens links.
- Grip grab, move, rotation and placement work.

Commit baseline for the successful v0.1 code path:
`9872fab3b1c0bd34eae2e56764e0f2ef2492a014`

Policy: preserve this renderer/WebView/depth path. Future features should be additive and must pass these regression checks.
