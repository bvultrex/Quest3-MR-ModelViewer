bl_info = {
    "name": "QuestMR Rig Animator",
    "author": "QuestMR Project",
    "version": (0, 2, 1),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > QuestMR",
    "description": "Focused GLB skeleton posing, keyframing and animation export",
    "category": "Animation",
}

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel
from mathutils import Matrix, Vector

ADDON_VERSION = "0.2.1"
ACTION_PREFIX = "QMRA_"
IK_COLLECTION_NAME = "QuestMR_IK"
IK_CONSTRAINT_PREFIX = "QMRA_IK_"
IK_HANDLE_PROP = "qmra_ik_handle"
IK_ROLE_PROP = "qmra_ik_role"
REF_COLLECTION_NAME = "QuestMR_Reference"
REF_OBJECT_PROP = "qmra_reference_object"
_pose_clipboard = {}


MIXAMO_ROLE_ALIASES = {
    "hips": ("hips", "pelvis"),
    "chest": ("spine2", "chest", "upperchest", "spine1"),
    "head": ("head",),
    "left_upper_arm": ("leftarm", "lupperarm", "upperarml"),
    "left_lower_arm": ("leftforearm", "lforearm", "lowerarml"),
    "left_hand": ("lefthand", "lhand", "handl"),
    "right_upper_arm": ("rightarm", "rupperarm", "upperarmr"),
    "right_lower_arm": ("rightforearm", "rforearm", "lowerarmr"),
    "right_hand": ("righthand", "rhand", "handr"),
    "left_upper_leg": ("leftupleg", "leftthigh", "lthigh", "upperlegl"),
    "left_lower_leg": ("leftleg", "leftshin", "lshin", "lowerlegl"),
    "left_foot": ("leftfoot", "lfoot", "footl"),
    "right_upper_leg": ("rightupleg", "rightthigh", "rthigh", "upperlegr"),
    "right_lower_leg": ("rightleg", "rightshin", "rshin", "lowerlegr"),
    "right_foot": ("rightfoot", "rfoot", "footr"),
}


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


def normalize_armature_display(armature):
    if armature is None:
        return
    armature.show_in_front = True
    try:
        armature.data.display_type = "STICK"
    except Exception:
        pass
    for pose_bone in armature.pose.bones:
        try:
            pose_bone.custom_shape = None
        except Exception:
            pass


def apply_pose_style(context, armature):
    if armature is None:
        return
    quest_pose = context.scene.qmra_pose_style == "QUEST"
    allow_root_motion = context.scene.qmra_allow_root_motion

    for pose_bone in armature.pose.bones:
        is_root = pose_bone.parent is None
        if quest_pose:
            can_translate = is_root and allow_root_motion
            pose_bone.lock_location = (
                not can_translate,
                not can_translate,
                not can_translate,
            )
            pose_bone.lock_scale = (True, True, True)
            pose_bone.lock_rotation = (False, False, False)
        else:
            pose_bone.lock_location = (False, False, False)
            pose_bone.lock_scale = (False, False, False)
            pose_bone.lock_rotation = (False, False, False)

    if quest_pose:
        try:
            context.scene.tool_settings.transform_pivot_point = "INDIVIDUAL_ORIGINS"
        except Exception:
            pass
        try:
            context.scene.transform_orientation_slots[0].type = "LOCAL"
        except Exception:
            pass
        try:
            if context.area and context.area.type == "VIEW_3D":
                bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
        except Exception:
            pass


def update_pose_style(self, context):
    armature = active_armature(context)
    if armature is not None:
        apply_pose_style(context, armature)


def ensure_pose_mode(context):
    armature = active_armature(context)
    if armature is None:
        return None
    select_armature(context, armature)
    normalize_armature_display(armature)
    try:
        bpy.ops.object.mode_set(mode="POSE")
    except RuntimeError:
        return None
    apply_pose_style(context, armature)
    return armature



def canonical_bone_name(name):
    value = "".join(ch.lower() for ch in name if ch.isalnum())
    for prefix in ("mixamorig", "mixamo", "armature"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value


def resolve_bone(armature, role):
    aliases = MIXAMO_ROLE_ALIASES.get(role, ())
    for pose_bone in armature.pose.bones:
        name = canonical_bone_name(pose_bone.name)
        for alias in aliases:
            if name == alias or name.startswith(alias):
                return pose_bone
    return None


def ik_handles():
    return [
        obj for obj in bpy.data.objects
        if bool(obj.get(IK_HANDLE_PROP, False))
    ]


def ik_constraints(armature):
    if armature is None:
        return []
    result = []
    for pose_bone in armature.pose.bones:
        for constraint in pose_bone.constraints:
            if constraint.name.startswith(IK_CONSTRAINT_PREFIX):
                result.append(constraint)
    return result


def has_ik_system(armature):
    return bool(ik_handles()) and bool(ik_constraints(armature))


def capture_pose_matrices(armature):
    if armature is None:
        return {}
    return {bone.name: bone.matrix.copy() for bone in armature.pose.bones}


def restore_pose_matrices(context, armature, matrices):
    if armature is None or not matrices:
        return
    for bone in armature.pose.bones:
        matrix = matrices.get(bone.name)
        if matrix is not None:
            try:
                bone.matrix = matrix
            except Exception:
                pass
    context.view_layer.update()


def reference_objects():
    return [
        obj for obj in bpy.data.objects
        if bool(obj.get(REF_OBJECT_PROP, False))
    ]


def ensure_reference_collection(context):
    collection = bpy.data.collections.get(REF_COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(REF_COLLECTION_NAME)
        context.scene.collection.children.link(collection)
    collection.hide_render = True
    return collection


def clear_reference_objects():
    for obj in list(reference_objects()):
        bpy.data.objects.remove(obj, do_unlink=True)
    collection = bpy.data.collections.get(REF_COLLECTION_NAME)
    if collection is not None and len(collection.objects) == 0:
        try:
            bpy.data.collections.remove(collection)
        except Exception:
            pass


def update_reference_opacity(self, context):
    alpha = context.scene.qmra_reference_opacity
    for obj in reference_objects():
        try:
            obj.color[3] = alpha
            obj.use_empty_image_alpha = True
        except Exception:
            pass


def update_reference_size(self, context):
    scale = context.scene.qmra_reference_size
    armature = active_armature(context)
    base = estimate_rig_height(armature) if armature is not None else 1.7
    for obj in reference_objects():
        try:
            obj.empty_display_size = base * scale
        except Exception:
            pass


def reference_center(armature):
    if armature is None or len(armature.pose.bones) == 0:
        return Vector((0.0, 0.0, 0.0))
    points = []
    for pose_bone in armature.pose.bones:
        points.append(rig_world_position(armature, pose_bone.head))
        points.append(rig_world_position(armature, pose_bone.tail))
    minimum = Vector((
        min(point.x for point in points),
        min(point.y for point in points),
        min(point.z for point in points),
    ))
    maximum = Vector((
        max(point.x for point in points),
        max(point.y for point in points),
        max(point.z for point in points),
    ))
    return (minimum + maximum) * 0.5


def ensure_ik_collection(context):
    collection = bpy.data.collections.get(IK_COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(IK_COLLECTION_NAME)
        context.scene.collection.children.link(collection)
    collection.hide_render = True
    return collection


def delete_ik_system(armature):
    if armature is not None:
        for pose_bone in armature.pose.bones:
            for constraint in list(pose_bone.constraints):
                if constraint.name.startswith(IK_CONSTRAINT_PREFIX):
                    pose_bone.constraints.remove(constraint)

    for obj in list(ik_handles()):
        bpy.data.objects.remove(obj, do_unlink=True)

    collection = bpy.data.collections.get(IK_COLLECTION_NAME)
    if collection is not None and len(collection.objects) == 0:
        try:
            bpy.data.collections.remove(collection)
        except Exception:
            pass


def rig_world_position(armature, value):
    return armature.matrix_world @ value


def rig_world_matrix(armature, pose_bone):
    return armature.matrix_world @ pose_bone.matrix


def estimate_rig_height(armature):
    points = []
    for pose_bone in armature.pose.bones:
        points.append(rig_world_position(armature, pose_bone.head))
        points.append(rig_world_position(armature, pose_bone.tail))
    if not points:
        return 1.7
    z_values = [point.z for point in points]
    height = max(z_values) - min(z_values)
    return max(height, 0.25)


def make_ik_handle(context, name, role, display_type, size, matrix_world, rotates=True):
    collection = ensure_ik_collection(context)
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.empty_display_type = display_type
    obj.empty_display_size = size
    obj.show_in_front = True
    obj.show_name = True
    obj.rotation_mode = "QUATERNION"
    obj.matrix_world = matrix_world.copy()
    obj[IK_HANDLE_PROP] = True
    obj[IK_ROLE_PROP] = role
    obj["qmra_ik_rotates"] = bool(rotates)
    return obj


def pole_position(armature, upper_bone, lower_bone, end_bone, distance_scale=0.75):
    root = rig_world_position(armature, upper_bone.head)
    joint = rig_world_position(armature, lower_bone.head)
    end = rig_world_position(armature, end_bone.head)

    axis = end - root
    axis_length = axis.length
    if axis_length < 1.0e-6:
        axis = rig_world_position(armature, lower_bone.tail) - root
        axis_length = axis.length
    if axis_length < 1.0e-6:
        axis = Vector((0.0, 0.0, 1.0))
        axis_length = 1.0
    axis.normalize()

    projected = root + axis * (joint - root).dot(axis)
    direction = joint - projected
    if direction.length < 1.0e-5:
        fallback = rig_world_matrix(armature, lower_bone).to_3x3() @ Vector((1.0, 0.0, 0.0))
        direction = fallback - axis * fallback.dot(axis)
    if direction.length < 1.0e-5:
        direction = Vector((0.0, -1.0, 0.0))
    direction.normalize()

    distance = max(axis_length * distance_scale, estimate_rig_height(armature) * 0.12)
    return joint + direction * distance


def create_limb_ik(
        context,
        armature,
        side_name,
        limb_name,
        upper_role,
        lower_role,
        end_role,
        target_role,
        pole_role):
    upper = resolve_bone(armature, upper_role)
    lower = resolve_bone(armature, lower_role)
    end = resolve_bone(armature, end_role)
    if upper is None or lower is None or end is None:
        missing = [
            role for role, bone in (
                (upper_role, upper),
                (lower_role, lower),
                (end_role, end),
            )
            if bone is None
        ]
        return False, missing

    base_size = estimate_rig_height(armature) * 0.035 * context.scene.qmra_ik_handle_scale

    target_matrix = rig_world_matrix(armature, end)
    target = make_ik_handle(
        context,
        f"QMRA_{side_name}_{limb_name}_Target",
        target_role,
        "CUBE",
        base_size,
        target_matrix,
        rotates=True,
    )

    pole_matrix = Matrix.Translation(pole_position(armature, upper, lower, end))
    pole = make_ik_handle(
        context,
        f"QMRA_{side_name}_{limb_name}_Pole",
        pole_role,
        "SPHERE",
        base_size * 0.72,
        pole_matrix,
        rotates=False,
    )

    ik = lower.constraints.new(type="IK")
    ik.name = IK_CONSTRAINT_PREFIX + target_role
    ik.target = target
    ik.pole_target = pole
    ik.chain_count = 2
    ik.use_location = True
    ik.use_rotation = False
    ik.use_stretch = False
    ik.iterations = 64
    ik.influence = 0.0

    copy_rotation = end.constraints.new(type="COPY_ROTATION")
    copy_rotation.name = IK_CONSTRAINT_PREFIX + target_role + "_ROT"
    copy_rotation.target = target
    copy_rotation.owner_space = "WORLD"
    copy_rotation.target_space = "WORLD"
    copy_rotation.mix_mode = "REPLACE"
    copy_rotation.influence = 0.0
    return True, []


def create_rotation_control(context, armature, role, handle_role, name):
    bone = resolve_bone(armature, role)
    if bone is None:
        return False

    base_size = estimate_rig_height(armature) * 0.042 * context.scene.qmra_ik_handle_scale
    control = make_ik_handle(
        context,
        name,
        handle_role,
        "ARROWS",
        base_size,
        rig_world_matrix(armature, bone),
        rotates=True,
    )

    copy_rotation = bone.constraints.new(type="COPY_ROTATION")
    copy_rotation.name = IK_CONSTRAINT_PREFIX + handle_role + "_ROT"
    copy_rotation.target = control
    copy_rotation.owner_space = "WORLD"
    copy_rotation.target_space = "WORLD"
    copy_rotation.mix_mode = "REPLACE"
    copy_rotation.influence = 0.0
    return True


def create_pelvis_control(context, armature):
    hips = resolve_bone(armature, "hips")
    if hips is None:
        return False

    base_size = estimate_rig_height(armature) * 0.05 * context.scene.qmra_ik_handle_scale
    control = make_ik_handle(
        context,
        "QMRA_Pelvis_Target",
        "pelvis",
        "CIRCLE",
        base_size,
        rig_world_matrix(armature, hips),
        rotates=True,
    )

    copy_location = hips.constraints.new(type="COPY_LOCATION")
    copy_location.name = IK_CONSTRAINT_PREFIX + "pelvis_LOC"
    copy_location.target = control
    copy_location.owner_space = "WORLD"
    copy_location.target_space = "WORLD"
    copy_location.influence = 0.0

    copy_rotation = hips.constraints.new(type="COPY_ROTATION")
    copy_rotation.name = IK_CONSTRAINT_PREFIX + "pelvis_ROT"
    copy_rotation.target = control
    copy_rotation.owner_space = "WORLD"
    copy_rotation.target_space = "WORLD"
    copy_rotation.mix_mode = "REPLACE"
    copy_rotation.influence = 0.0
    return True


def update_ik_influence(self, context):
    armature = active_armature(context)
    if armature is None:
        return
    influence = context.scene.qmra_ik_influence
    for constraint in ik_constraints(armature):
        constraint.influence = influence


def calibrate_pole_angle(context, armature, ik_constraint, desired_head, desired_tail):
    owner = None
    for pose_bone in armature.pose.bones:
        if ik_constraint in pose_bone.constraints[:]:
            owner = pose_bone
            break
    if owner is None or ik_constraint.type != "IK" or ik_constraint.pole_target is None:
        return

    import math

    # Keep every QuestMR constraint disabled except the chain currently being calibrated.
    all_constraints = ik_constraints(armature)
    for constraint in all_constraints:
        constraint.influence = 0.0

    best_angle = 0.0
    best_error = float("inf")

    def test(angle):
        ik_constraint.pole_angle = angle
        ik_constraint.influence = 1.0
        context.view_layer.update()
        error = (owner.head - desired_head).length + (owner.tail - desired_tail).length
        ik_constraint.influence = 0.0
        return error

    samples = 32
    step = (2.0 * math.pi) / samples
    for index in range(samples):
        angle = -math.pi + index * step
        error = test(angle)
        if error < best_error:
            best_error = error
            best_angle = angle

    refine_step = step / 6.0
    for offset in range(-6, 7):
        angle = best_angle + offset * refine_step
        error = test(angle)
        if error < best_error:
            best_error = error
            best_angle = angle

    ik_constraint.pole_angle = best_angle
    ik_constraint.influence = 0.0
    context.view_layer.update()


def activate_ik_from_current_pose(context, armature):
    if armature is None or not has_ik_system(armature):
        return False

    # Start from the deform rig exactly as it currently looks.
    for constraint in ik_constraints(armature):
        constraint.influence = 0.0
    context.view_layer.update()

    snap_ik_handles_to_pose(context, armature)
    context.view_layer.update()

    desired = {
        bone.name: (bone.head.copy(), bone.tail.copy())
        for bone in armature.pose.bones
    }

    # Pole-angle calibration makes the two-bone solver choose the same bend
    # plane as the existing pose before IK takes ownership.
    for pose_bone in armature.pose.bones:
        for constraint in pose_bone.constraints:
            if (
                constraint.name.startswith(IK_CONSTRAINT_PREFIX)
                and constraint.type == "IK"
                and constraint.pole_target is not None
            ):
                head, tail = desired[pose_bone.name]
                calibrate_pole_angle(context, armature, constraint, head, tail)

    context.scene.qmra_ik_influence = 1.0
    for constraint in ik_constraints(armature):
        constraint.influence = 1.0
    context.view_layer.update()
    return True


def key_ik_handles(context):
    handles = ik_handles()
    if not handles:
        return 0

    frame = context.scene.frame_current
    interpolation = context.scene.qmra_interpolation
    prefs = context.preferences.edit
    old_interpolation = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = interpolation
    try:
        for handle in handles:
            handle.keyframe_insert(data_path="location", frame=frame)
            if bool(handle.get("qmra_ik_rotates", False)):
                handle.keyframe_insert(data_path="rotation_quaternion", frame=frame)
    finally:
        prefs.keyframe_new_interpolation_type = old_interpolation
    return len(handles)


def snap_ik_handles_to_pose(context, armature):
    handles_by_role = {
        obj.get(IK_ROLE_PROP): obj
        for obj in ik_handles()
    }
    if not handles_by_role:
        return 0

    constraints = ik_constraints(armature)
    old_influences = [(constraint, constraint.influence) for constraint in constraints]
    for constraint, _ in old_influences:
        constraint.influence = 0.0
    context.view_layer.update()

    role_to_bone = {
        "hand_l": "left_hand",
        "hand_r": "right_hand",
        "foot_l": "left_foot",
        "foot_r": "right_foot",
        "pelvis": "hips",
        "chest": "chest",
        "head": "head",
    }
    changed = 0
    for handle_role, bone_role in role_to_bone.items():
        handle = handles_by_role.get(handle_role)
        bone = resolve_bone(armature, bone_role)
        if handle is not None and bone is not None:
            handle.matrix_world = rig_world_matrix(armature, bone)
            changed += 1

    pole_specs = (
        ("elbow_l", "left_upper_arm", "left_lower_arm", "left_hand"),
        ("elbow_r", "right_upper_arm", "right_lower_arm", "right_hand"),
        ("knee_l", "left_upper_leg", "left_lower_leg", "left_foot"),
        ("knee_r", "right_upper_leg", "right_lower_leg", "right_foot"),
    )
    for handle_role, upper_role, lower_role, end_role in pole_specs:
        handle = handles_by_role.get(handle_role)
        upper = resolve_bone(armature, upper_role)
        lower = resolve_bone(armature, lower_role)
        end = resolve_bone(armature, end_role)
        if handle is not None and upper is not None and lower is not None and end is not None:
            handle.location = pole_position(armature, upper, lower, end)
            changed += 1

    for constraint, influence in old_influences:
        constraint.influence = influence
    context.view_layer.update()
    return changed

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


def rotation_data_path(bone):
    if bone.rotation_mode == "QUATERNION":
        return "rotation_quaternion"
    if bone.rotation_mode == "AXIS_ANGLE":
        return "rotation_axis_angle"
    return "rotation_euler"


def key_paths_for_bone(context, bone):
    if context.scene.qmra_pose_style == "QUEST":
        paths = [rotation_data_path(bone)]
        if bone.parent is None and context.scene.qmra_allow_root_motion:
            paths.insert(0, "location")
        return paths
    return ["location", rotation_data_path(bone), "scale"]


def key_pose_bone(context, bone, frame):
    for data_path in key_paths_for_bone(context, bone):
        bone.keyframe_insert(data_path=data_path, frame=frame, group=bone.name)


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
                disable_bone_shape=True,
                guess_original_bind_pose=False,
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
        for imported_armature in armatures:
            normalize_armature_display(imported_armature)
        select_armature(context, armature)
        context.scene.qmra_source_glb = self.filepath
        context.scene.render.fps = context.scene.qmra_fps
        context.scene.frame_start = context.scene.qmra_frame_start
        context.scene.frame_end = context.scene.qmra_frame_end
        bpy.ops.object.mode_set(mode="POSE")
        apply_pose_style(context, armature)
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



class QMRA_OT_create_ik(Operator):
    bl_idname = "qmra.create_ik"
    bl_label = "Create / Rebuild IK Handles"
    bl_description = "Create Quest-style IK controls for a Mixamo-compatible humanoid rig"

    def execute(self, context):
        armature = ensure_pose_mode(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}

        preserved_pose = capture_pose_matrices(armature)
        delete_ik_system(armature)
        context.view_layer.update()
        restore_pose_matrices(context, armature, preserved_pose)

        # Handles are created with all QuestMR constraints disabled.
        # Building/rebuilding the control layer must never change the visible pose.
        context.scene.qmra_ik_influence = 0.0

        missing = []
        created = 0
        limb_specs = (
            ("L", "Hand", "left_upper_arm", "left_lower_arm", "left_hand", "hand_l", "elbow_l"),
            ("R", "Hand", "right_upper_arm", "right_lower_arm", "right_hand", "hand_r", "elbow_r"),
            ("L", "Foot", "left_upper_leg", "left_lower_leg", "left_foot", "foot_l", "knee_l"),
            ("R", "Foot", "right_upper_leg", "right_lower_leg", "right_foot", "foot_r", "knee_r"),
        )
        for spec in limb_specs:
            ok, limb_missing = create_limb_ik(context, armature, *spec)
            if ok:
                created += 2
            else:
                missing.extend(limb_missing)

        if create_pelvis_control(context, armature):
            created += 1
        if create_rotation_control(context, armature, "chest", "chest", "QMRA_Chest_Target"):
            created += 1
        if create_rotation_control(context, armature, "head", "head", "QMRA_Head_Target"):
            created += 1

        context.view_layer.update()
        if created == 0:
            self.report({"ERROR"}, "No compatible Mixamo-style humanoid bones were detected")
            return {"CANCELLED"}

        restore_pose_matrices(context, armature, preserved_pose)
        context.view_layer.update()

        if missing:
            unique = ", ".join(sorted(set(missing)))
            self.report({"WARNING"}, f"Handles created safely; missing roles: {unique}")
        else:
            self.report({"INFO"}, f"Created {created} controls without changing the pose")
        return {"FINISHED"}


class QMRA_OT_activate_ik(Operator):
    bl_idname = "qmra.activate_ik"
    bl_label = "Activate IK From Current Pose"
    bl_description = "Snap controls to the current pose, calibrate limb bend planes, then enable IK"

    def execute(self, context):
        armature = active_armature(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}
        if not has_ik_system(armature):
            self.report({"ERROR"}, "Create IK handles first")
            return {"CANCELLED"}

        if not activate_ik_from_current_pose(context, armature):
            self.report({"ERROR"}, "Could not activate IK")
            return {"CANCELLED"}

        self.report({"INFO"}, "IK activated from the current pose")
        return {"FINISHED"}


class QMRA_OT_remove_ik(Operator):
    bl_idname = "qmra.remove_ik"
    bl_label = "Remove IK Handles"
    bl_description = "Remove QuestMR IK controls and constraints without deleting the model"

    def execute(self, context):
        armature = active_armature(context)
        delete_ik_system(armature)
        context.view_layer.update()
        self.report({"INFO"}, "QuestMR IK controls removed")
        return {"FINISHED"}


class QMRA_OT_snap_ik(Operator):
    bl_idname = "qmra.snap_ik"
    bl_label = "Snap Handles to Pose"
    bl_description = "Move IK handles onto the current unconstrained armature pose"

    def execute(self, context):
        armature = active_armature(context)
        if armature is None:
            self.report({"ERROR"}, "No armature found")
            return {"CANCELLED"}
        count = snap_ik_handles_to_pose(context, armature)
        if count == 0:
            self.report({"ERROR"}, "No IK controls found")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Snapped {count} IK controls to current pose")
        return {"FINISHED"}


class QMRA_OT_key_ik(Operator):
    bl_idname = "qmra.key_ik"
    bl_label = "Key IK Pose"
    bl_description = "Key all QuestMR IK targets at the current frame"

    def execute(self, context):
        count = key_ik_handles(context)
        if count == 0:
            self.report({"ERROR"}, "No IK controls found")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Keyed {count} IK controls at frame {context.scene.frame_current}")
        return {"FINISHED"}

class QMRA_OT_load_reference(Operator):
    bl_idname = "qmra.load_reference"
    bl_label = "Load Reference Image / Clip"
    bl_description = "Load a still image or movie as a viewport reference"

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tif;*.tiff;*.mp4;*.mov;*.avi;*.mkv;*.webm",
        options={"HIDDEN"},
    )

    def execute(self, context):
        if not self.filepath:
            return {"CANCELLED"}

        armature = active_armature(context)
        center = reference_center(armature)
        size = (estimate_rig_height(armature) if armature is not None else 1.7)
        size *= context.scene.qmra_reference_size

        before = set(obj.name for obj in bpy.data.objects)
        try:
            bpy.ops.object.empty_image_add(
                filepath=self.filepath,
                align="VIEW",
                location=center,
                background=False,
                check_existing=True,
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Reference load failed: {exc}")
            return {"CANCELLED"}

        created = [
            obj for obj in bpy.data.objects
            if obj.name not in before and obj.type == "EMPTY" and obj.empty_display_type == "IMAGE"
        ]
        obj = created[-1] if created else context.object
        if obj is None:
            self.report({"ERROR"}, "Blender did not create a reference image object")
            return {"CANCELLED"}

        # Move reference into a dedicated non-rendering collection.
        collection = ensure_reference_collection(context)
        for current_collection in list(obj.users_collection):
            current_collection.objects.unlink(obj)
        collection.objects.link(obj)

        obj.name = "QMRA_Reference"
        obj[REF_OBJECT_PROP] = True
        obj.empty_display_size = size
        obj.empty_image_depth = "BACK"
        obj.empty_image_side = "DOUBLE_SIDED"
        obj.show_in_front = False
        obj.use_empty_image_alpha = True
        obj.color[3] = context.scene.qmra_reference_opacity
        obj.hide_render = True

        # Movie/image-sequence references follow the Blender scene timeline.
        try:
            obj.image_user.use_auto_refresh = True
            obj.image_user.frame_start = context.scene.frame_start
        except Exception:
            pass

        context.scene.qmra_reference_path = self.filepath
        context.scene.qmra_reference_name = obj.data.name if obj.data else "Reference"
        self.report({"INFO"}, f"Loaded reference: {context.scene.qmra_reference_name}")
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class QMRA_OT_clear_reference(Operator):
    bl_idname = "qmra.clear_reference"
    bl_label = "Remove References"
    bl_description = "Remove QuestMR viewport reference images and clips"

    def execute(self, context):
        clear_reference_objects()
        context.scene.qmra_reference_path = ""
        context.scene.qmra_reference_name = ""
        self.report({"INFO"}, "Reference media removed")
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

        if context.scene.qmra_key_ik_with_pose and has_ik_system(armature):
            count = key_ik_handles(context)
            self.report({"INFO"}, f"Keyed {count} IK controls at frame {frame}")
            return {"FINISHED"}

        # This preference controls newly-created curves. We also normalize the
        # keys at this frame afterwards so subsequent keys use the requested mode.
        prefs = context.preferences.edit
        old_interpolation = prefs.keyframe_new_interpolation_type
        prefs.keyframe_new_interpolation_type = interpolation
        try:
            for bone in bones:
                key_pose_bone(context, bone, frame)
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
            paths = key_paths_for_bone(context, bone)
            for path in paths:
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
            quest_pose = context.scene.qmra_pose_style == "QUEST"
            if not quest_pose or (bone.parent is None and context.scene.qmra_allow_root_motion):
                bone.location = (0.0, 0.0, 0.0)
            if not quest_pose:
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

        armature = active_armature(context)
        using_ik = has_ik_system(armature)

        original_selection = [obj for obj in context.selected_objects]
        original_active = context.view_layer.objects.active
        if using_ik:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in context.scene.objects:
                if not bool(obj.get(IK_HANDLE_PROP, False)):
                    obj.select_set(True)
            if armature is not None:
                context.view_layer.objects.active = armature

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
            "export_animation_mode": "SCENE" if using_ik else "ACTIONS",
            "export_force_sampling": True,
            "export_sampling_interpolation_fallback": "LINEAR",
            "export_reset_pose_bones": True,
            "export_anim_single_armature": True,
            "export_bake_animation": using_ik,
            "use_selection": using_ik,
        }
        for key, value in optional.items():
            if key in props:
                kwargs[key] = value

        try:
            bpy.ops.export_scene.gltf(**kwargs)
        except Exception as exc:
            self.report({"ERROR"}, f"GLB export failed: {exc}")
            return {"CANCELLED"}
        finally:
            if using_ik:
                bpy.ops.object.select_all(action="DESELECT")
                for obj in original_selection:
                    if obj.name in bpy.data.objects:
                        obj.select_set(True)
                if original_active is not None and original_active.name in bpy.data.objects:
                    context.view_layer.objects.active = original_active

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
        io.separator()
        io.label(text="Pose Controls", icon="ORIENTATION_LOCAL")
        io.prop(scene, "qmra_pose_style", expand=True)
        if scene.qmra_pose_style == "QUEST":
            io.prop(scene, "qmra_allow_root_motion", text="Allow Root Translation")
            io.label(text="Bones rotate around their own joints.")
            io.label(text="Translation + scale are locked on child bones.")
        else:
            io.label(text="Free Pose allows G / R / S on all bones.")

        reference = layout.box()
        reference.label(text="2 • Reference", icon="IMAGE_DATA")
        reference.operator("qmra.load_reference", icon="FILE_IMAGE")
        row = reference.row(align=True)
        row.prop(scene, "qmra_reference_opacity", text="Opacity", slider=True)
        row.prop(scene, "qmra_reference_size", text="Size")
        if scene.qmra_reference_name:
            reference.label(text=f"Loaded: {scene.qmra_reference_name}")
            reference.label(text="Movie references follow the scene timeline.")
            reference.operator("qmra.clear_reference", icon="X")
        else:
            reference.label(text="Load a still image or video clip for manual matching.")

        ik = layout.box()
        ik.label(text="3 • IK Handles", icon="CON_KINEMATIC")
        ik.prop(scene, "qmra_ik_influence", text="IK Influence", slider=True)
        ik.prop(scene, "qmra_ik_handle_scale", text="Handle Size")
        ik.prop(scene, "qmra_key_ik_with_pose", text="Key IK with Key Pose")
        ik.operator("qmra.create_ik", text="Create / Rebuild Handles (Safe)", icon="CON_KINEMATIC")
        ik.operator("qmra.activate_ik", text="Activate IK From Current Pose", icon="PLAY")
        row = ik.row(align=True)
        row.operator("qmra.snap_ik", icon="SNAP_ON")
        row.operator("qmra.key_ik", icon="KEY_HLT")
        ik.operator("qmra.remove_ik", icon="X")
        if armature and has_ik_system(armature):
            state = "ACTIVE" if scene.qmra_ik_influence > 0.001 else "READY / DISABLED"
            ik.label(text=f"{state}: {len(ik_handles())} controls")
            ik.label(text="Cubes = hands/feet • spheres = elbow/knee poles")
            ik.label(text="Circle = pelvis • arrows = chest/head")
        else:
            ik.label(text="Create handles after importing a Mixamo humanoid.")

        clip = layout.box()
        clip.label(text="4 • Animation Clip", icon="ACTION")
        clip.prop(scene, "qmra_clip_name", text="Name")
        clip.operator("qmra.new_clip", icon="ADD")
        row = clip.row(align=True)
        row.prop(scene, "qmra_frame_start", text="Start")
        row.prop(scene, "qmra_frame_end", text="End")
        clip.prop(scene, "qmra_fps", text="FPS")
        clip.operator("qmra.apply_timeline", icon="CHECKMARK")

        timeline = layout.box()
        timeline.label(text="5 • Pose + Keyframes", icon="KEY_HLT")
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
        if scene.qmra_pose_style == "QUEST":
            if armature and has_ik_system(armature):
                timeline.label(text="Viewport: move IK handles with G; rotate end targets with R.")
            else:
                timeline.label(text="Viewport: select a bone and rotate it (R / rotate gizmo).")
        else:
            timeline.label(text="Viewport: select bones, then G / R / S to pose.")

        out = layout.box()
        out.label(text="6 • Export", icon="EXPORT")
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
    QMRA_OT_create_ik,
    QMRA_OT_activate_ik,
    QMRA_OT_remove_ik,
    QMRA_OT_snap_ik,
    QMRA_OT_key_ik,
    QMRA_OT_load_reference,
    QMRA_OT_clear_reference,
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
    bpy.types.Scene.qmra_pose_style = EnumProperty(
        name="Pose Style",
        description="Choose Quest-like rotation-only posing or unrestricted Blender transforms",
        items=(
            (
                "QUEST",
                "Quest Pose",
                "Rotate child bones around their own joint pivots; lock translation and scale",
            ),
            (
                "FREE",
                "Free Pose",
                "Allow normal Blender location, rotation and scale transforms",
            ),
        ),
        default="QUEST",
        update=update_pose_style,
    )
    bpy.types.Scene.qmra_allow_root_motion = BoolProperty(
        name="Allow Root Translation",
        description="Let the skeleton root move while child bones stay rotation-only",
        default=True,
        update=update_pose_style,
    )
    bpy.types.Scene.qmra_ik_influence = FloatProperty(
        name="IK Influence",
        description="Blend QuestMR IK controls with the underlying armature animation",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        update=update_ik_influence,
    )
    bpy.types.Scene.qmra_ik_handle_scale = FloatProperty(
        name="Handle Size",
        description="Viewport size multiplier for QuestMR IK controls",
        default=1.0,
        min=0.25,
        max=3.0,
    )
    bpy.types.Scene.qmra_key_ik_with_pose = BoolProperty(
        name="Key IK with Key Pose",
        description="When IK controls exist, Key Pose keys the controls instead of deform bones",
        default=True,
    )
    bpy.types.Scene.qmra_reference_path = StringProperty(
        name="Reference Path",
        default="",
    )
    bpy.types.Scene.qmra_reference_name = StringProperty(
        name="Reference Name",
        default="",
    )
    bpy.types.Scene.qmra_reference_opacity = FloatProperty(
        name="Reference Opacity",
        default=0.55,
        min=0.05,
        max=1.0,
        subtype="FACTOR",
        update=update_reference_opacity,
    )
    bpy.types.Scene.qmra_reference_size = FloatProperty(
        name="Reference Size",
        default=1.0,
        min=0.2,
        max=4.0,
        update=update_reference_size,
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
        "qmra_pose_style",
        "qmra_allow_root_motion",
        "qmra_ik_influence",
        "qmra_ik_handle_scale",
        "qmra_key_ik_with_pose",
        "qmra_reference_path",
        "qmra_reference_name",
        "qmra_reference_opacity",
        "qmra_reference_size",
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
