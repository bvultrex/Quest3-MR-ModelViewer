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


## 2026-09-25 — v0.2.0 IK control layer

Implemented the first non-destructive Mixamo-oriented IK authoring layer.

Architecture:
- original Mixamo bones remain deformation/export bones
- QuestMR creates external Empty controls in a dedicated `QuestMR_IK` collection
- generated constraints are prefixed `QMRA_IK_`
- helper objects carry semantic roles for future image/video pose reconstruction

Controls:
- left/right hand target + elbow pole
- left/right foot target + knee pole
- pelvis position/rotation control
- optional chest rotation control
- optional head rotation control

IK chains:
- IK constraint lives on forearm / lower leg
- chain_count = 2
- stretching disabled
- hand/foot end bones receive target world rotation
- pole positions are initialized from the current limb plane

Animation:
- Key IK Pose keys target object transforms
- Key Pose automatically keys IK controls while Key IK with Key Pose is enabled
- IK Influence blends helper constraints with underlying bone animation
- Snap Handles to Pose temporarily disables QuestMR constraints, reads the unconstrained pose, moves the controls, then restores influence

Export:
- QuestMR IK controls are excluded using glTF Selected Objects export
- constraint-driven motion uses glTF sampling / Bake All Objects Animations
- IK exports use SCENE animation mode so the evaluated pose is exported as seen
- the GLB contains model, skin and baked pose animation, not the helper control objects

Future Pose-from-Reference code should target semantic IK roles rather than deform-bone transforms.


## 2026-09-25 — v0.2.1 pose-safe IK and reference media

User feedback:
- Create / Rebuild IK changed the existing pose.
- IK controls were difficult to identify/select.
- no visible UI existed yet for reference images or video clips.

Changes:
- preserve evaluated armature pose across IK rebuild
- all newly generated QuestMR constraints start at 0% influence
- Create / Rebuild is now pose-neutral
- new Activate IK From Current Pose operator
- limb pole-angle calibration searches for the angle that best reproduces the current elbow/knee bend before enabling IK
- direct Quick Select buttons for semantic IK roles
- reference-media loader for still images and movies
- reference media uses a dedicated non-rendering QuestMR_Reference collection
- reference opacity and size controls
- movie/image references use Blender Image Empty playback and follow scene frames

Important:
Automatic body landmark detection is not part of v0.2.1 yet. This release establishes the reference media layer and stable semantic IK targets needed for the next Pose-from-Reference milestone.
