# BrowserPanel experiment v0.2

Base: Quest3 MR Model Viewer v1.0.1 hardware-accepted final.

## v0.1 hardware checkpoint

Quest 3 hardware acceptance confirmed:
- Wikipedia is fully visible with no right-edge crop.
- Browser text is sharp.
- Environment Depth occlusion works.
- Controller trigger opens links.
- Grip moves and rotates the panel correctly.

This v0.1 result is the golden BrowserPanel baseline. v0.2 must preserve it.

## v0.2 scope

- keep fixed 2560x1600 WebView / SurfaceTexture producer
- slim browser toolbar: Back, Forward, Reload, URL field, GO
- URL field requests the Quest system keyboard
- proportional spatial resize from all four corners
- resize hit zones live OUTSIDE the visible browser image
- no permanent resize indicator overlays the webpage
- a small hover marker may appear outside the selected corner
- the opposite corner remains fixed while resizing
- direct body Grip still moves and rotates the entire panel
- existing Viewer Environment Depth path remains unchanged

Resize is intentionally proportional in v0.2. This preserves the known-good 1.6 WebView backing aspect and avoids reopening the historical SurfaceTexture crop/stretch problem.

## v0.2 hardware acceptance

1. All v0.1 acceptance points still pass.
2. Each outer corner can be targeted just beyond the browser edge.
3. Grip on that outer corner resizes proportionally and keeps the opposite corner anchored.
4. No permanent resize handle appears inside webpage content.
5. Back, Forward and Reload work.
6. URL field receives focus, keyboard can be opened, and GO / Enter navigates to the typed URL.

Tabs, favorites, downloads and free-aspect resize remain out of scope.


## v0.2.1 hotfix

Hardware feedback from v0.2:
- proportional resize itself works
- outer resize hover indicator was not visible enough
- Quest system keyboard did not appear for the offscreen VirtualDisplay EditText

v0.2.1 changes:
- keep the proven resize hit geometry unchanged
- replace the tiny hover dot with a bright cyan L-shaped corner bracket outside the webpage
- stop depending on the Quest/Android system IME for URL entry
- add an in-panel QWERTZ URL keyboard with backspace, URL punctuation, GO and HIDE


## v0.2.2 system keyboard experiment

Hardware feedback from v0.2.1:
- outer resize hover indicators are now visible and resize still works
- custom in-panel URL keyboard works, but it is not suitable as the primary browser keyboard
- users need the normal Quest keyboard, numbers/symbols and input in arbitrary HTML fields

v0.2.2:
- enables the Horizon/VrShell overlay keyboard feature used by reprojected Android UI
- restores Android IME input for the URL EditText
- URL EditText requests URI keyboard semantics and IME GO
- after browser clicks, editable HTML input/textarea/contentEditable focus is detected and the WebView requests the system keyboard
- the custom QWERTZ panel remains compiled only as fallback code but is kept hidden
