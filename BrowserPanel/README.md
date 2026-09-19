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


## v0.2.3 Activity IME proxy

Hardware feedback from v0.2.2:
- the system keyboard still did not appear
- the custom keyboard was hidden as intended, leaving no keyboard at all

Root cause hypothesis:
- the editable URL/WebView controls live on the offscreen VirtualDisplay Presentation
- Horizon's system IME overlay expects a real input connection attached to the primary immersive Activity window

v0.2.3:
- creates a hidden 2x2 EditText on the real Activity window as an IME proxy
- URL bar clicks mirror text/selection into that proxy and request the Quest system keyboard
- focused HTML input/textarea/contentEditable fields are detected and mirrored through the same proxy
- edits are mirrored back into the URL bar or active web element
- number, tel, email, URL and password HTML input types are mapped to appropriate Android input types
- the offscreen Presentation EditText no longer owns the system IME


## v0.2.4 joystick scroll + precision aim

Hardware feedback from v0.2.3:
- Quest system keyboard now works
- resize and outer-corner indicators work
- pages cannot be scrolled from the controller
- controller aim ray is too jittery / imprecise for comfortable browser use

v0.2.4:
- adds a native per-hand OpenXR thumbstick VECTOR2F action
- the thumbstick on the controller currently aiming at the browser scrolls vertically
- 18% deadzone plus smooth progressive scroll speed for fine and fast movement
- adds adaptive UV stabilization to damp small controller jitter without making large movements sluggish
- the visible reticle and WebView click use exactly the same filtered coordinates
- reticle is slightly smaller to show the actual click target more precisely
- keyboard, resize, WebView producer and Environment Depth paths are otherwise unchanged


## v0.2.5 Browser Comfort

Hardware feedback from v0.2.4:
- joystick scrolling works well
- precision aim works well
- browser core, Quest keyboard, resize, placement and Environment Depth are all confirmed working

v0.2.5:
- removes the legacy GLB Viewer tablet UI from room rendering and interaction
- keeps the proven Viewer renderer/depth plumbing underneath to avoid destabilizing BrowserPanel
- adds Home button (Wikipedia)
- adds Reset Window button: standard size and respawn in front of the current head pose
- adds page Zoom -, 100%, +
- adds persistent favorites with star toggle and a compact FAV strip
- stores up to 8 favorites
- keeps v0.2.4 pointer, scroll, keyboard, resize and Environment Depth paths unchanged


## v0.2.6 Quest-style pointer surface

Hardware feedback from v0.2.5:
- browser content interaction works
- the visual pointer disappears over the URL bar / browser chrome

v0.2.6:
- retires the world-space cube reticle used as the BrowserPanel cursor
- keeps the proven OpenXR aim pose, adaptive stabilization and click coordinates
- draws a Quest-style ring/dot cursor directly in the Android BrowserPanel surface
- cursor is drawn by the root layout after WebView, URL bar, favorites and toolbar
- visual cursor never participates in Android hit testing
- sends an explicit hover-exit when the controller ray leaves the browser
- resize corner indicators remain native and unchanged

Meta managed pointer systems live in higher-level Interaction SDK / IWSDK stacks; this native OpenXR project keeps its lightweight input path rather than migrating frameworks only for cursor visuals.
