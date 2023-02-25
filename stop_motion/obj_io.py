# Copyright 2022 Bassam Kurdali / urchn.org
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
"""
Operators that thinly wrap Blender's wavefront obj Import/Export directly
as Stop Motion targets. See https://www.srcxor.org/blog/3d-glitching/ to
understand why this exists :)
"""

if "bpy" in locals():
    import importlib
    importlib.reload(modifier_data)
    importlib.reload(modes)
else:
    from . import modifier_data
    from . import modes

import bpy
import os
from .modifier_data import Modifier, StopMotionOperator


def path(context):
    return context.blend_data.filepath.replace(
        ".blend", f"_{context.object.name}_frame.obj")

class OBJECT_OT_import_stop_motion_obj(StopMotionOperator):
    """Import obj as a key drawing"""
    bl_idname = "object.import_stop_motion_obj"
    bl_label = "Import OBJ"

    def execute(self, context):
        filepath = path(context)
        if not os.path.isfile(filepath):
            self.report({'WARNING'}, "No OBJ; Export something first")
            return {'CANCELLED'}
        stop_motion_object = context.object
        preferences = context.preferences.addons[__package__].preferences

        bpy.ops.wm.obj_import(
            filepath=filepath,
            clamp_size=0,

            forward_axis='Y', up_axis='Z',

            import_vertex_groups=False, validate_meshes=False)


        imported_objects = bpy.context.selected_objects


        stop_motion_object.select_set(True)
        context.view_layer.objects.active = stop_motion_object

        bpy.ops.object.keyframe_stop_motion(use_copy=False)
        for ob in imported_objects:
            if ob is not stop_motion_object:
                bpy.data.objects.remove(ob, do_unlink=True)

        return {'FINISHED'}


class OBJECT_OT_export_stop_motion_obj(StopMotionOperator):
    """Export current frame as an obj"""
    bl_idname = "object.export_stop_motion_obj"
    bl_label = "Export OBJ"

    def execute(self, context):

        if not context.blend_data.filepath:
            self.report({'WARNING'}, "Save Blend file first")
            return {'CANCELLED'}
        stop_motion_object = context.object
        filepath = path(context)
        selected_objects = [ob for ob in context.selected_objects]
        preferences = context.preferences.addons[__package__].preferences
        mode = stop_motion_object.mode
        modes.set_object(mode)
        data = Modifier(stop_motion_object).get_object().data

        export_object = bpy.data.objects.new(
            name=f"{stop_motion_object.name}_export",object_data=data)
        context.collection.objects.link(export_object)

        stop_motion_object.select_set(False)
        export_object.select_set(True)
        context.view_layer.objects.active = export_object

        # stop_motion_object.data = data
        # export obj with the right settings

        bpy.ops.wm.obj_export(
            filepath=filepath,
            path_mode='AUTO',
            check_existing=False,
            export_selected_objects=True,
            export_animation=False,
            forward_axis='Y', up_axis='Z', global_scale=1,

            apply_modifiers=False, export_eval_mode='DAG_EVAL_VIEWPORT',

            export_triangulated_mesh=False, export_curves_as_nurbs=False,
            export_object_groups=False,
            export_material_groups=False,


            export_uv=preferences.use_uvs,
            export_normals=preferences.use_normals,
            export_colors=preferences.use_colors,
            export_materials=preferences.use_materials,

            export_vertex_groups=preferences.use_vertex_groups,
            export_smooth_groups=preferences.use_smooth_groups,
            smooth_group_bitflags=False,)

        bpy.data.objects.remove(export_object)

        stop_motion_object.select_set(True)
        context.view_layer.objects.active = stop_motion_object


        modes.restore(mode, stop_motion_object)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_OT_import_stop_motion_obj)
    bpy.utils.register_class(OBJECT_OT_export_stop_motion_obj)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_import_stop_motion_obj)
    bpy.utils.unregister_class(OBJECT_OT_export_stop_motion_obj)

if __name__ == "__main__":
    register()
