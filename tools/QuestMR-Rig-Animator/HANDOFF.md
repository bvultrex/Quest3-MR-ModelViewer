# HANDOFF — QuestMR Rig Animator

## Goal

A deliberately simplified animation authoring companion for rigged GLB files used by Quest3 MR Model Viewer.

## Current version

v0.1.0

## Technology

Blender 4.4+ extension.

Blender is used as the GLB/skinning/animation backend. The QuestMR extension supplies the focused UX and project-specific export path.

## Implemented

- Import rigged .glb
- detect armature
- Pose Mode / in-front bones
- create named animation Action
- configure frame range and FPS
- pose with standard Blender viewport transforms
- key Selected Bones or Whole Rig
- Step / Linear / Smooth interpolation
- copy/paste/reset pose
- delete current-frame keys
- playback
- export animated .glb

## Next technical milestones

1. Hardware/desktop acceptance on a real project GLB.
2. Clip browser for multiple Actions.
3. IK controller creation for hands and feet.
4. Retarget helper.
5. Dedicated QuestMR workspace with reduced Blender chrome.
6. Packaged Windows launcher.
7. Later Quest-native authoring prototype.

## Important design choice

Do not merge authoring into Quest3 MR Model Viewer unless there is a specific runtime need. Keep the viewer lean and use shared GLB animation conventions as the bridge between projects.


## v0.1.2 pose policy

Default authoring mode is **Quest Pose**:
- non-root bones: rotation only
- root: rotation + optional translation
- no child-bone scale/location keyframes
- Individual Origins + Local orientation

**Free Pose** restores unrestricted location/rotation/scale for advanced corrections.
