# Build architecture state

Current app baseline: **v1.0.1 accepted final release**

The GitHub Actions workflow is intentionally thin. Build logic lives in `scripts/`:

- `patch_depth.py` - filtered Environment Depth + MSAA quality pass
- `patch_lighting.py` - lighting uniforms and controls
- `patch_android_picker.py` - Android document picker / native app bridge
- `parts/patch_glb_loader.*.pyfrag` - cgltf GLB loader and viewer foundations
- `parts/patch_glb_safety.*.pyfrag` - transactional import and safety validation
- `parts/patch_tablet_ui.*.pyfrag` - labelled room-spawned tablet UI
- `parts/patch_pbr.*.pyfrag` - normals, UVs and PBR texture path
- `parts/patch_v037.*` through `patch_v045.*` - controls, safe import path, dual-controller input and direct tablet/model grab
- `parts/patch_v046.*.pyfrag` - first v1 import-state text plus raw metre-scale experiment
- `parts/patch_v047.*.pyfrag` - v1.0.1 physical SIZE presets and OpenGL scene-lifecycle hardening
- `apply_patches.sh` - reconstructs/applies patches and verifies expected markers
- `brand_android.sh` - package/version/label branding
- `verify_apk.sh` - artifact collection and APK verification

Pinned dependencies: Meta OpenXR SDK v85, cgltf v1.15, stb `2c980bb59875b0d32144a71867fbdebb2f77cd20`.

## Interaction model

Either controller can point and trigger-click the UI. Trigger-hold operates sliders. Either controller can Grip/Squeeze the tablet or imported model with preserved pickup offset and full 6DoF pose.

## Import behavior

- Persisted `questmr_import.glb` is ignored on cold start.
- Picker transactions clear stale app-private source before selection.
- Successful picker selection creates the only source eligible for a fresh import.
- Import state text: IDLE / WAIT / READY / ERROR.

## Scaling behavior

Default FIT scale targets about 34 cm maximum extent before the manual SCALE multiplier.

v1.0.1 does not assume source GLB coordinates represent intended metres. `SIZE` sets the model's largest displayed dimension explicitly:

- FIT
- 32 mm
- 75 mm
- 150 mm
- 300 mm

Manual SCALE returns SIZE to FIT.

## GL lifecycle rule

v1.0.0 hardware testing exposed stale static OpenGL object names across XR/scene restart. Static UI mesh wrappers could retain `built=true` after their EGL-context resources were invalid. A later GL allocation could reuse the same numeric name, plausibly explaining both missing labels and the observed white artifact.

v1.0.1 therefore:

- invalidates all static UI mesh wrappers on `Scene::Create`,
- clears imported-model GL handles on `Scene::Create` while preserving only the safe import stamp,
- explicitly releases UI text GL resources on `Scene::Destroy`,
- explicitly destroys imported-model GL resources on `Scene::Destroy`.

Never preserve raw VAO/VBO/IBO/texture object names across a scene/EGL lifecycle boundary.

## Hardware acceptance

Quest 3 final acceptance confirms:

- UI text remains present after app restart,
- the prior white import artifact is no longer observed with known-good GLBs,
- SIZE presets behave plausibly,
- SCALE returns physical SIZE to FIT,
- tablet/model grabbing remains stable,
- safe cold start remains intact.

## Hardware findings / safety envelope

Quest 3 confirms Environment Depth, GLB picker, PBR, dual-controller UI, direct tablet/model grip and smooth ~100k-class models. A 3.03M-triangle model causes severe sustained XR/system lag.

Current guards: 192 MiB GLB, 3M vertices, 12M indices, **2M triangles**, 4096px texture edge, 160 MiB mipmapped textures, 256 MiB estimated GPU resources, 384 MiB estimated CPU import working set.

Do not raise the 2M ceiling without LOD, simplification or another renderer-side strategy.

**Frozen v1.0 baseline: v1.0.1 accepted final.** Any new feature work should branch from this state as v1.1+ rather than modifying the accepted v1.0 baseline conceptually.
