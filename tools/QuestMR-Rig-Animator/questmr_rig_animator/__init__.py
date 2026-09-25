bl_info = {
    "name": "QuestMR Rig Animator",
    "author": "QuestMR Project",
    "version": (0, 1, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > QuestMR",
    "description": "Focused GLB skeleton posing, keyframing and animation export",
    "category": "Animation",
}

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel

ADDON_VERSION = "0.1.0"
ACTION_PREFIX = "QMRA_"
_pose_clipboard = {}


def active_armature(context):
    obj = context.object
    if obj and obj.type == "ARMATURE":
        return obj
    for candidate in context.selected_objects:
        if candidate.type == "ARMATURE":
            return candidate
    for candidate in context.scene.objects:
        if candidate.type == "ARMATURE":
            return candidate
    return None


def select_armature(context, armature):
    if armature is None:
        return
    if context.object and context.object.mode != "OBJECT":
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except RuntimeError:
            pass
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    context.view_layer.objects.active = armature
    armature.show_in_front = True
    armature.data.show_names = context.scene.qmra_show_bone_names


def ensure_pose_mode(context):
    armature = active_armature(context)
    if armature is None:
        return None
    select_armature(context, armature)
    try:
        bpy.ops.object.mode_set(mode="POSE")
    except RuntimeError:
        return None
    return armature


def action_fcurves(armature):
    if armature is None or armature.animation_data is None:
        return []
    action = armature.animation_data.action
    if action is None:
        return []

    # Blender 4.4+ layered Action API.
    try:
        from bpy_extras.anim_utils import animdata_get_channelbag_for_assigned_slot
        channelbag = animdata_get_channelbag_for_assigned_slot(armature.animation_data)
        if channelbag is not None:
            return list(channelbag.fcurves)
    except Exception:
        pass

    # Compatibility path for legacy Actions.
    return list(getattr(action, "fcurves", []))


def key_pose_bone(bone, frame):
    bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
    if bone.rotation_mode == "QUATERNION":
        bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=bone.name)
    elif bone.rotation_mode == "AXIS_ANGLE":
        bone.keyframe_insert(data_path="rotation_axis_angle", frame=frame, group=bone.name)
    else:
        bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone.name)
    bone.keyframe_insert(data_path="scale", frame=frame, group=bone.name)


def apply_interpolation_at_frame(armature, frame, interpolation):
    for curve in action_fcurves(armature):
        changed = False
        for key in curve.keyframe_points:
            if abs(key.co.x - frame) < 0.0001:
                key.interpolation = interpolation
                changed = True
        if changed:
            curve.update()


class QMRA_OT_import_glb(Operator):
    bl_idname = "qmra.import_glb"
    bl_label = "Import GLB"
    bl_description = "Import a rigged GLB and prepare its armature for animation"

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.glb", options={"HIDDEN"})

    def execute(self, context):
        if not self.filepath.lower().endswith(".glb"):
            self.report({"ERROR"}, "QuestMR Rig Animator accepts .glb files only")
            return {"CANCELLED"}

        if context.scene.qmra_clear_scene_on_import:
            if context.object and context.object.mode != "OBJECT":
                try:
                    bpy.ops.object.mode_set(mode="OBJECT")
                except RuntimeError:
                    pass
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete(use_global=False)

        before = set(obj.name for obj in bpy.data.objects)
        try:
            bpy.ops.import_scene.gltf(
                filepath=self.filepath,
                bone_heuristic="BLENDER",
                import_select_created_objects=True,
            )
        except Exception as exc:
            self.report({"ERROR"}, f"GLB import failed: {exc}")
            return {"CANCELLED"}

        new_objects = [obj for obj in bpy.data.objects if obj.name not in before]
        armatures = [obj for obj in new_objects if obj.type == "ARMATURE"]
        if not armatures:
            armatures = [obj for obj in context.selected_objects if obj.type == "ARMATURE"]
        if not armatures:
            self.report({"ERROR"}, "GLB imported, but no armature/skeleton was found")
            return {"CANCELLED"}

        armature = armatures[0]
        select_armature(context, armature)
        context.scene.qmra_source_glb = self.filepath
        context.scene.render.fps = context.scene.qmra_fps
        context.scene.frame_start = context.scene.qmra_frame_start
        context.scene.frame_end = context.scene.qmra_frame_end
        bpy.ops.object.mode_set(mode="POSE")
        self.report({"INFO"}, f"Ready: {armature.name} ({len(armature.data.bones)} bones)")
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class QMRA_OT_prepare_rig(Operator):
    bl_idname = "qmra.prepare_rig"
    bl_label = "Pose Rig"
    bl_description = "Select the detected armature and enter Pose Mode"

    def execute(self, context):
        armature = ensure_pose_mode(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Pose Mode: {armature.name}")
        return {"FINISHED"}


class QMRA_OT_new_clip(Operator):
    bl_idname = "qmra.new_clip"
    bl_label = "New Animation Clip"
    bl_description = "Create and activate a new Action for the current rig"

    def execute(self, context):
        armature = active_armature(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}

        name = context.scene.qmra_clip_name.strip() or "Animation"
        if not name.startswith(ACTION_PREFIX):
            name = ACTION_PREFIX + name
        action = bpy.data.actions.new(name=name)

        armature.animation_data_create()
        armature.animation_data.action = action
        if hasattr(action, "use_frame_range"):
            action.use_frame_range = True
            action.frame_start = context.scene.qmra_frame_start
            action.frame_end = context.scene.qmra_frame_end

        context.scene.frame_start = context.scene.qmra_frame_start
        context.scene.frame_end = context.scene.qmra_frame_end
        context.scene.render.fps = context.scene.qmra_fps
        context.scene.frame_set(context.scene.qmra_frame_start)
        ensure_pose_mode(context)
        self.report({"INFO"}, f"Created clip: {action.name}")
        return {"FINISHED"}


class QMRA_OT_key_pose(Operator):
    bl_idname = "qmra.key_pose"
    bl_label = "Key Pose"
    bl_description = "Insert transform keys for the selected bones or the whole rig"

    def execute(self, context):
        armature = ensure_pose_mode(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}

        if armature.animation_data is None or armature.animation_data.action is None:
            bpy.ops.qmra.new_clip()
        if armature.animation_data is None or armature.animation_data.action is None:
            self.report({"ERROR"}, "Could not create an animation clip")
            return {"CANCELLED"}

        if context.scene.qmra_key_scope == "SELECTED":
            bones = list(context.selected_pose_bones or [])
            if not bones:
                self.report({"ERROR"}, "Select at least one pose bone, or choose Whole Rig")
                return {"CANCELLED"}
        else:
            bones = list(armature.pose.bones)

        frame = context.scene.frame_current
        interpolation = context.scene.qmra_interpolation

        # This preference controls newly-created curves. We also normalize the
        # keys at this frame afterwards so subsequent keys use the requested mode.
        prefs = context.preferences.edit
        old_interpolation = prefs.keyframe_new_interpolation_type
        prefs.keyframe_new_interpolation_type = interpolation
        try:
            for bone in bones:
                key_pose_bone(bone, frame)
            apply_interpolation_at_frame(armature, frame, interpolation)
        finally:
            prefs.keyframe_new_interpolation_type = old_interpolation

        self.report({"INFO"}, f"Keyed {len(bones)} bones at frame {frame}")
        return {"FINISHED"}


class QMRA_OT_delete_pose_keys(Operator):
    bl_idname = "qmra.delete_pose_keys"
    bl_label = "Delete Keys @ Frame"
    bl_description = "Delete pose transform keys at the current frame"

    def execute(self, context):
        armature = ensure_pose_mode(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}

        bones = (
            list(context.selected_pose_bones or [])
            if context.scene.qmra_key_scope == "SELECTED"
            else list(armature.pose.bones)
        )
        if not bones:
            self.report({"ERROR"}, "No bones selected")
            return {"CANCELLED"}

        frame = context.scene.frame_current
        for bone in bones:
            for path in ("location", "rotation_quaternion", "rotation_axis_angle", "rotation_euler", "scale"):
                try:
                    bone.keyframe_delete(data_path=path, frame=frame, group=bone.name)
                except Exception:
                    pass
        self.report({"INFO"}, f"Deleted keys at frame {frame}")
        return {"FINISHED"}


class QMRA_OT_copy_pose(Operator):
    bl_idname = "qmra.copy_pose"
    bl_label = "Copy Pose"

    def execute(self, context):
        global _pose_clipboard
        armature = ensure_pose_mode(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}

        bones = list(context.selected_pose_bones or armature.pose.bones)
        _pose_clipboard = {bone.name: bone.matrix_basis.copy() for bone in bones}
        self.report({"INFO"}, f"Copied {len(_pose_clipboard)} bone transforms")
        return {"FINISHED"}


class QMRA_OT_paste_pose(Operator):
    bl_idname = "qmra.paste_pose"
    bl_label = "Paste Pose"

    def execute(self, context):
        armature = ensure_pose_mode(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}
        if not _pose_clipboard:
            self.report({"ERROR"}, "Pose clipboard is empty")
            return {"CANCELLED"}

        pasted = 0
        for name, matrix in _pose_clipboard.items():
            bone = armature.pose.bones.get(name)
            if bone is not None:
                bone.matrix_basis = matrix.copy()
                pasted += 1
        context.view_layer.update()
        self.report({"INFO"}, f"Pasted {pasted} bone transforms")
        return {"FINISHED"}


class QMRA_OT_reset_pose(Operator):
    bl_idname = "qmra.reset_pose"
    bl_label = "Reset Pose"
    bl_description = "Reset selected bones or the whole rig to its rest transform"

    def execute(self, context):
        armature = ensure_pose_mode(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}

        bones = (
            list(context.selected_pose_bones or [])
            if context.scene.qmra_key_scope == "SELECTED"
            else list(armature.pose.bones)
        )
        if not bones:
            self.report({"ERROR"}, "No bones selected")
            return {"CANCELLED"}

        for bone in bones:
            bone.location = (0.0, 0.0, 0.0)
            bone.scale = (1.0, 1.0, 1.0)
            if bone.rotation_mode == "QUATERNION":
                bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
            elif bone.rotation_mode == "AXIS_ANGLE":
                bone.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
            else:
                bone.rotation_euler = (0.0, 0.0, 0.0)
        context.view_layer.update()
        return {"FINISHED"}


class QMRA_OT_apply_timeline(Operator):
    bl_idname = "qmra.apply_timeline"
    bl_label = "Apply Timeline"

    def execute(self, context):
        scene = context.scene
        scene.frame_start = scene.qmra_frame_start
        scene.frame_end = scene.qmra_frame_end
        scene.render.fps = scene.qmra_fps

        armature = active_armature(context)
        action = armature.animation_data.action if armature and armature.animation_data else None
        if action is not None and hasattr(action, "use_frame_range"):
            action.use_frame_range = True
            action.frame_start = scene.qmra_frame_start
            action.frame_end = scene.qmra_frame_end
        return {"FINISHED"}


class QMRA_OT_step_frame(Operator):
    bl_idname = "qmra.step_frame"
    bl_label = "Step Frame"

    delta: IntProperty(default=1)

    def execute(self, context):
        scene = context.scene
        target = max(scene.frame_start, min(scene.frame_end, scene.frame_current + self.delta))
        scene.frame_set(target)
        return {"FINISHED"}


class QMRA_OT_export_glb(Operator):
    bl_idname = "qmra.export_glb"
    bl_label = "Export Animated GLB"
    bl_description = "Export the current scene as GLB with skinning and animation Actions"

    filepath: StringProperty(subtype="FILE_PATH")
    filename_ext = ".glb"
    filter_glob: StringProperty(default="*.glb", options={"HIDDEN"})

    def execute(self, context):
        filepath = self.filepath
        if not filepath.lower().endswith(".glb"):
            filepath += ".glb"

        if context.object and context.object.mode != "OBJECT":
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except RuntimeError:
                pass

        kwargs = {
            "filepath": filepath,
            "export_format": "GLB",
            "export_animations": True,
            "export_skins": True,
            "export_yup": True,
            "export_frame_range": False,
        }

        # Keep the extension compatible across Blender 4.4+ / 5.x where the
        # glTF operator gained additional animation settings.
        try:
            props = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
        except Exception:
            props = set()
        optional = {
            "export_animation_mode": "ACTIONS",
            "export_force_sampling": True,
            "export_sampling_interpolation_fallback": "LINEAR",
            "export_reset_pose_bones": True,
            "export_anim_single_armature": True,
        }
        for key, value in optional.items():
            if key in props:
                kwargs[key] = value

        try:
            bpy.ops.export_scene.gltf(**kwargs)
        except Exception as exc:
            self.report({"ERROR"}, f"GLB export failed: {exc}")
            return {"CANCELLED"}

        context.scene.qmra_last_export = filepath
        self.report({"INFO"}, f"Exported animated GLB: {filepath}")
        return {"FINISHED"}

    def invoke(self, context, event):
        source = context.scene.qmra_source_glb
        if source and source.lower().endswith(".glb"):
            self.filepath = source[:-4] + "_animated.glb"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class QMRA_PT_main(Panel):
    bl_label = "QuestMR Rig Animator"
    bl_idname = "QMRA_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "QuestMR"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = active_armature(context)

        header = layout.box()
        header.label(text=f"Rig Animator v{ADDON_VERSION}", icon="ARMATURE_DATA")
        if armature:
            header.label(text=f"Rig: {armature.name} • {len(armature.data.bones)} bones")
            action = armature.animation_data.action if armature.animation_data else None
            header.label(text=f"Clip: {action.name if action else 'none'}")
        else:
            header.label(text="No armature detected")

        io = layout.box()
        io.label(text="1 • Model", icon="IMPORT")
        io.prop(scene, "qmra_clear_scene_on_import")
        io.operator("qmra.import_glb", icon="FILE_FOLDER")
        row = io.row(align=True)
        row.operator("qmra.prepare_rig", icon="POSE_HLT")
        row.prop(scene, "qmra_show_bone_names", text="Bone Names")

        clip = layout.box()
        clip.label(text="2 • Animation Clip", icon="ACTION")
        clip.prop(scene, "qmra_clip_name", text="Name")
        clip.operator("qmra.new_clip", icon="ADD")
        row = clip.row(align=True)
        row.prop(scene, "qmra_frame_start", text="Start")
        row.prop(scene, "qmra_frame_end", text="End")
        clip.prop(scene, "qmra_fps", text="FPS")
        clip.operator("qmra.apply_timeline", icon="CHECKMARK")

        timeline = layout.box()
        timeline.label(text="3 • Pose + Keyframes", icon="KEY_HLT")
        timeline.prop(scene, "qmra_key_scope", expand=True)
        timeline.prop(scene, "qmra_interpolation", expand=True)
        timeline.prop(scene, "frame_current", text="Frame")
        row = timeline.row(align=True)
        back = row.operator("qmra.step_frame", text="-1")
        back.delta = -1
        row.operator("screen.animation_play", text="Play / Pause", icon="PLAY")
        forward = row.operator("qmra.step_frame", text="+1")
        forward.delta = 1

        row = timeline.row(align=True)
        row.operator("qmra.key_pose", icon="KEY_HLT")
        row.operator("qmra.delete_pose_keys", icon="KEY_DEHLT")

        row = timeline.row(align=True)
        row.operator("qmra.copy_pose", icon="COPYDOWN")
        row.operator("qmra.paste_pose", icon="PASTEDOWN")
        timeline.operator("qmra.reset_pose", icon="LOOP_BACK")
        timeline.label(text="Viewport: select bones, then G / R / S to pose.")

        out = layout.box()
        out.label(text="4 • Export", icon="EXPORT")
        out.operator("qmra.export_glb", icon="EXPORT")
        if scene.qmra_last_export:
            out.label(text="Last export:")
            out.label(text=scene.qmra_last_export)


def update_bone_names(self, context):
    armature = active_armature(context)
    if armature:
        armature.data.show_names = context.scene.qmra_show_bone_names


classes = (
    QMRA_OT_import_glb,
    QMRA_OT_prepare_rig,
    QMRA_OT_new_clip,
    QMRA_OT_key_pose,
    QMRA_OT_delete_pose_keys,
    QMRA_OT_copy_pose,
    QMRA_OT_paste_pose,
    QMRA_OT_reset_pose,
    QMRA_OT_apply_timeline,
    QMRA_OT_step_frame,
    QMRA_OT_export_glb,
    QMRA_PT_main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.qmra_source_glb = StringProperty(name="Source GLB", default="")
    bpy.types.Scene.qmra_last_export = StringProperty(name="Last Export", default="")
    bpy.types.Scene.qmra_clip_name = StringProperty(name="Clip Name", default="Animation")
    bpy.types.Scene.qmra_frame_start = IntProperty(name="Start", default=1, min=0, max=100000)
    bpy.types.Scene.qmra_frame_end = IntProperty(name="End", default=90, min=1, max=100000)
    bpy.types.Scene.qmra_fps = IntProperty(name="FPS", default=30, min=1, max=240)
    bpy.types.Scene.qmra_clear_scene_on_import = BoolProperty(
        name="Clear Scene on Import",
        description="Delete the current scene objects before importing the GLB",
        default=True,
    )
    bpy.types.Scene.qmra_show_bone_names = BoolProperty(
        name="Names",
        description="Display bone names in the 3D viewport",
        default=False,
        update=update_bone_names,
    )
    bpy.types.Scene.qmra_key_scope = EnumProperty(
        name="Key Scope",
        items=(
            ("SELECTED", "Selected", "Key only selected pose bones"),
            ("ALL", "Whole Rig", "Key every pose bone"),
        ),
        default="SELECTED",
    )
    bpy.types.Scene.qmra_interpolation = EnumProperty(
        name="Interpolation",
        items=(
            ("CONSTANT", "Step", "Hold each pose until the next keyframe"),
            ("LINEAR", "Linear", "Straight interpolation between poses"),
            ("BEZIER", "Smooth", "Bezier interpolation for eased motion"),
        ),
        default="LINEAR",
    )


def unregister():
    for attr in (
        "qmra_source_glb",
        "qmra_last_export",
        "qmra_clip_name",
        "qmra_frame_start",
        "qmra_frame_end",
        "qmra_fps",
        "qmra_clear_scene_on_import",
        "qmra_show_bone_names",
        "qmra_key_scope",
        "qmra_interpolation",
    ):
        if hasattr(bpy.types.Scene, attr):
            delattr(bpy.types.Scene, attr)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
