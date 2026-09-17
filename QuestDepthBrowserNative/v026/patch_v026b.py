from pathlib import Path

ROOT = Path('meta-openxr-sdk/Samples/XrSamples/XrPassthroughOcclusion')
JAVA = ROOT / 'java/com/oculus/xrpassthroughocclusion/QuestDepthBrowserBridge.java'

text = JAVA.read_text()
old = '''            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                    width, height, Gravity.CENTER);
            contentFrame.setLayoutParams(params);
'''
new = '''            // Anchor to the known producer pixels, not Presentation's measured
            // width. On Quest the Presentation decor can report a wider logical
            // area than the SurfaceTexture actually captures.
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                    width, height, Gravity.TOP | Gravity.LEFT);
            params.leftMargin = Math.max(0, (surfaceWidth - width) / 2);
            params.topMargin = Math.max(0, (surfaceHeight - height) / 2);
            contentFrame.setLayoutParams(params);
'''
if old not in text:
    raise SystemExit('v0.2.6b viewport positioning anchor missing')
text = text.replace(old, new, 1)
JAVA.write_text(text)
print('v0.2.6b: browser viewport anchored to producer pixel coordinates')
