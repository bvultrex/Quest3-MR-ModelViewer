from pathlib import Path
import re

root = Path('meta-openxr-sdk')

# v0.3.3: keep the android_app bridge in the translation unit that is
# actually linked into libxrpassthroughocclusion.so.
main_cpp = root / 'Samples/XrSamples/XrPassthroughOcclusion/Src/XrPassthroughOcclusion.cpp'
text = main_cpp.read_text()

if 'QuestMrGetAndroidApp' not in text:
    anchor = 'using namespace OVR;\n'
    if anchor not in text:
        raise SystemExit('XrPassthroughOcclusion.cpp namespace anchor not found')
    bridge = r'''
#if defined(ANDROID)
// Quest3 MR Model Viewer v0.3.3 native app bridge.
static struct android_app* gQuestMrAndroidApp = nullptr;
extern "C" struct android_app* QuestMrGetAndroidApp() {
    return gQuestMrAndroidApp;
}
#endif

'''
    text = text.replace(anchor, anchor + bridge, 1)

main_re = re.compile(
    r'(void\s+android_main\(\s*struct\s+android_app\*\s*androidApp\s*\)\s*\{)'
)
if 'gQuestMrAndroidApp = androidApp;' not in text:
    text, count = main_re.subn(
        r'\1\n    gQuestMrAndroidApp = androidApp;',
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit('Could not patch android_main(android_app*)')

main_cpp.write_text(text)

android_root = root / 'Samples/XrSamples/XrPassthroughOcclusion/Projects/Android'
build_gradle = android_root / 'build.gradle'
manifest_path = android_root / 'AndroidManifest.xml'

# v0.3.3 intentionally does NOT search for or modify Meta's MainActivity.
# A tiny dedicated Activity owns the Storage Access Framework roundtrip instead.
java_root = android_root / 'questmr/java/com/bvultrex/quest3mrmodelviewer'
java_root.mkdir(parents=True, exist_ok=True)
picker = java_root / 'QuestMrPickerActivity.java'
picker.write_text(r'''package com.bvultrex.quest3mrmodelviewer;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

public class QuestMrPickerActivity extends Activity {
    private static final int QUESTMR_OPEN_GLB = 4242;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[] {
            "model/gltf-binary",
            "model/gltf+json",
            "application/octet-stream"
        });
        try {
            startActivityForResult(intent, QUESTMR_OPEN_GLB);
        } catch (Exception ignored) {
            finish();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != QUESTMR_OPEN_GLB || resultCode != RESULT_OK || data == null) {
            finish();
            return;
        }

        Uri uri = data.getData();
        if (uri == null) {
            finish();
            return;
        }

        File dir = getFilesDir();
        File temp = new File(dir, "questmr_import.tmp");
        File target = new File(dir, "questmr_import.glb");
        try (InputStream input = getContentResolver().openInputStream(uri);
             OutputStream output = new FileOutputStream(temp)) {
            if (input == null) {
                finish();
                return;
            }
            byte[] buffer = new byte[65536];
            int count;
            while ((count = input.read(buffer)) > 0) {
                output.write(buffer, 0, count);
            }
            output.flush();

            if (target.exists() && !target.delete()) {
                finish();
                return;
            }
            if (!temp.renameTo(target)) {
                try (InputStream retryInput = new FileInputStream(temp);
                     OutputStream retryOutput = new FileOutputStream(target)) {
                    while ((count = retryInput.read(buffer)) > 0) {
                        retryOutput.write(buffer, 0, count);
                    }
                    retryOutput.flush();
                }
                temp.delete();
            }
        } catch (Exception ignored) {
            temp.delete();
        }
        finish();
    }
}
''')

# Explicitly include our generated Java source directory even if the Meta sample
# customizes its sourceSets.
gradle = build_gradle.read_text()
marker = '// QUESTMR_V033_PICKER_SOURCESET'
if marker not in gradle:
    gradle += '''

// QUESTMR_V033_PICKER_SOURCESET
android {
    sourceSets {
        main {
            java.srcDir 'questmr/java'
        }
    }
}
'''
    build_gradle.write_text(gradle)

# Register the helper Activity. It is internal-only and immediately delegates to
# Android's system document picker.
manifest = manifest_path.read_text()
activity_marker = '<!-- QUESTMR_V033_PICKER_ACTIVITY -->'
if activity_marker not in manifest:
    entry = '''
        <!-- QUESTMR_V033_PICKER_ACTIVITY -->
        <activity
            android:name="com.bvultrex.quest3mrmodelviewer.QuestMrPickerActivity"
            android:exported="false"
            android:excludeFromRecents="true"
            android:theme="@android:style/Theme.Translucent.NoTitleBar" />
'''
    close = manifest.rfind('</application>')
    if close < 0:
        raise SystemExit('AndroidManifest application closing tag not found')
    manifest = manifest[:close] + entry + manifest[close:]
    manifest_path.write_text(manifest)

print('Patched linked sample android_app bridge:', main_cpp)
print('Created dedicated GLB picker Activity:', picker)
print('Registered dedicated picker in manifest:', manifest_path)
