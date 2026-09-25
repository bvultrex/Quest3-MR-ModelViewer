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


### v0.2.1 Quest Pose

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


## v0.2.0 IK Handles

QuestMR now creates a non-destructive IK control layer on top of a Mixamo-compatible deform rig.

### Controls

- **Hand L / Hand R**: cube targets. Move with G to place the wrist; rotate with R to orient the hand.
- **Elbow L / Elbow R**: sphere pole targets controlling elbow bend direction.
- **Foot L / Foot R**: cube targets. Move with G to place the ankle; rotate with R to orient the foot.
- **Knee L / Knee R**: sphere pole targets controlling knee bend direction.
- **Pelvis**: circle target controlling hips position + orientation.
- **Chest**: arrows target controlling upper torso orientation when a matching bone is present.
- **Head**: arrows target controlling head orientation.

### Workflow

1. Import the rigged GLB.
2. Click **Create / Rebuild IK Handles**.
3. Create a new animation clip.
4. Move hand/foot/pelvis controls and elbow/knee pole controls.
5. Rotate hand/foot/chest/head targets when needed.
6. Change frame.
7. Press **Key Pose**. With **Key IK with Key Pose** enabled, all IK controls are keyed.
8. Repeat.
9. Export Animated GLB.

IK constraints use two-bone chains with stretching disabled. The exported GLB does not contain the QuestMR helper empties; the glTF exporter samples the constraint-driven armature into the exported animation.

This control layout is also the API target for the planned Pose-from-Reference system: image/video pose detection will set these same control transforms rather than manipulating deform bones directly.


## v0.2.1 Pose-safe IK + Reference Media

### Pose-safe handle creation

**Create / Rebuild Handles (Safe)** no longer takes ownership of the current pose.

- the currently evaluated pose is captured
- old QuestMR IK constraints/handles are removed
- the pose matrices are restored
- new controls are created with QuestMR constraints at 0% influence
- the visible pose therefore remains unchanged

Use **Activate IK From Current Pose** when you are ready. It:
- snaps all controls onto the current deform-rig pose
- estimates elbow/knee pole directions
- automatically searches a pole angle that best preserves the existing bend
- then enables QuestMR IK at 100%

### Quick Select

The IK panel now includes direct selection buttons for:
- L/R Hand
- L/R Foot
- Pelvis
- Head
- L/R Elbow pole
- L/R Knee pole

Selecting a position control switches to Blender's Move tool. Head/Chest rotation controls use the Rotate tool.

### Reference images and clips

A new **Reference** section accepts still images and movie files.

- Load Reference Image / Clip
- PNG/JPG/JPEG/WebP/BMP/TIFF
- MP4/MOV/AVI/MKV/WebM
- opacity control
- size control
- Remove References
- the reference is created as a non-rendering Image Empty aligned to the current viewport
- movie references follow the Blender scene timeline

This is the visual-reference layer for the planned automatic pose reconstruction. v0.2.1 does not yet run body-joint detection; it adds the upload/display workflow first.
