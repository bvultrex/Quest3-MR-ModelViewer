# QuestMR Rig Animator

Focused Windows animation authoring companion for **Quest3 MR Model Viewer**.

## v0.1.0

The first build is intentionally a Blender extension instead of a new rendering engine. Blender owns GLB import/export, armatures, skinning and animation data; QuestMR adds a compact workflow for people who want to pose a rig and make clips without living in Blender's full animation UI.

### Current workflow

1. Install the extension ZIP in Blender 4.4+.
2. Open **3D View > Sidebar > QuestMR**.
3. **Import GLB**. The extension uses Blender's glTF round-trip bone heuristic.
4. Click **New Animation Clip**.
5. Select bones in the viewport and use Blender's normal **G / R / S** transforms.
6. Move the QuestMR frame control.
7. Press **Key Pose**.
8. Repeat for additional poses.
9. Use **Play / Pause** to preview.
10. **Export Animated GLB**.

### v0.1 features

- GLB-only import dialog
- automatic rig detection
- automatic Pose Mode setup
- armature drawn in front of the mesh
- optional bone names
- named animation Action creation
- Start / End / FPS controls
- Selected Bones or Whole Rig keying
- Step / Linear / Smooth interpolation
- pose copy/paste
- reset pose
- delete current-frame pose keys
- frame stepping and playback
- animated GLB export with skinning and Actions
- safe output name suggestion: `*_animated.glb`

### Architecture

QuestMR Rig Animator does not modify the Quest viewer runtime. It is a sibling authoring tool.

For v0.1 the 3D editor is Blender itself. That keeps GLB round-tripping, skinning, materials, inverse bind matrices and animation export on a mature implementation instead of duplicating them in a new Windows renderer.

### Planned

- clip browser and rename/duplicate/delete
- per-key pose list
- visual IK handles for hands and feet
- two-bone IK helper setup
- mirror pose
- loop/cycle toggle
- root motion controls
- retarget/import animation from another rig
- multi-character scene authoring
- contact/anchor helpers
- simplified custom workspace
- packaged Windows launcher
- later Quest authoring UI using controller grabs


### v0.1.2 Quest Pose

Quest Pose is now the default authoring mode and mirrors the interaction philosophy of the MR viewer.

- child-bone Location is locked
- child-bone Scale is locked
- Rotation remains editable
- each selected bone rotates around its own origin
- transform orientation is Local
- Blender's rotate tool is selected automatically where possible
- the root bone may optionally retain Translation for root motion
- Key Pose writes Rotation only for child bones in Quest Pose
- root Location is keyed only when Allow Root Translation is enabled
- Free Pose remains available for unrestricted Blender G / R / S editing

This prevents accidental joint translation from stretching the skinned mesh while posing.
