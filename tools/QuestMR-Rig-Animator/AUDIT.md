# AUDIT

## 2026-09-25 — v0.1.0 bootstrap

Created QuestMR Rig Animator as a sibling authoring tool inside the Quest3-MR-ModelViewer repository.

Decision: do not add authoring complexity to the Quest runtime. Use Blender as the Windows animation backend first, with QuestMR providing a focused sidebar workflow.

Implemented:
- GLB import with BLENDER glTF bone heuristic
- rig detection and Pose Mode setup
- new animation Action creation
- key pose insertion for location / rotation / scale
- Selected vs Whole Rig scope
- Step / Linear / Smooth interpolation
- copy / paste / reset pose
- timeline setup, stepping and playback
- animated GLB export
- Blender 4.4+ layered Action F-Curve compatibility path

Preservation rule:
- Quest3 MR Model Viewer remains a playback/runtime project.
- Rig Animator changes must not change viewer GLB import safety or XR rendering behavior.


## 2026-09-25 — v0.1.1 Mixamo GLB import display fix

Observed: a Mixamo-skeleton GLB appeared in Blender as several deformed sphere/blob shapes.

Correction:
- keep the Mixamo skeleton as the runtime/export skeleton
- import glTF with `disable_bone_shape=True`
- import with `guess_original_bind_pose=False` as the safer default
- defensively clear all imported `PoseBone.custom_shape`
- force the armature viewport display to `STICK`

Rationale: Blender's default glTF armature presentation can create custom bone shapes for display. Those shapes are not the skinned character mesh and should not be used as the QuestMR authoring presentation.


## 2026-09-25 — v0.1.2 Quest-style rotation posing

User feedback: manually moving pose-bone pivots with Blender transforms stretched/morphed the entire skinned mesh. Desired behavior matches the MR viewer: joints should rotate around their pivot rather than translate through the mesh.

Implemented:
- new Quest Pose / Free Pose selector
- Quest Pose is default
- child pose-bone Location locked
- child pose-bone Scale locked
- Rotation remains unlocked
- root Location optionally allowed for root motion
- Individual Origins pivot mode
- Local transform orientation
- rotate tool selected automatically in View3D where possible
- Quest Pose keyframes write Rotation only for child bones
- root Location is keyed only when explicitly allowed
- Reset/Delete Keys respect Quest Pose channel policy

Free Pose preserves Blender's unrestricted transform behavior for exceptional cases.
