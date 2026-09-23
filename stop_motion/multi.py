# Copyright 2026 Ursula Kurdali / urchn.org
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

if "bpy" in locals():
    import importlib
    importlib.reload(update_handler)
    importlib.reload(modifier_data)
    importlib.reload(version)
    importlib.reload(modes)
else:
    from . import update_handler
    from . import modifier_data
    from . import version
    from . import modes

import bpy
import os
from .modifier_data import Modifier, StopMotionOperator

"""
TODO:
materials multi set
disable onion skins if active

"""

COLLECTION_NAME = "MULTITEMP"


class Multiples(StopMotionOperator):
    """Enter Mode for multiple Frames"""
    bl_options = {'REGISTER', 'UNDO'}

    def set_mode(self):
        pass

    def execute(self, context):
        stopmo = context.object
        modifier = Modifier(stopmo)
        if not modifier:
            return {'CANCELED'}
        frame_objects = modifier.selected_keyframes_objects()
        if not frame_objects:
            return {'CANCELED'}
        if stopmo.onion_skin_settings.enable:
            stopmo.onion_skin_settings.enable = False
            scene.multiple_stop_motion_settings.restore_onionskins = True
        collection = bpy.data.collections.new(COLLECTION_NAME)
        context.collection.children.link(collection)
        for frame_object in frame_objects:
            collection.objects.link(frame_object)
            frame_object.select_set(state=True)
        stopmo.select_set(state=False)
        context.view_layer.objects.active = frame_objects[0]
        context.scene.multiple_stop_motion_settings.editing = True
        context.scene.multiple_stop_motion_settings.stopmo_object = stopmo.name
        self.set_mode(modifier)
        return {'FINISHED'}


class OBJECT_OT_stop_motion_edit_multiples(Multiples):
    """ Enter Edit Mode"""
    bl_idname = "object.stop_motion_edit_multiples"
    bl_label = "Edit Multiples"

    def set_mode(self, modifier):
        modes.set_edit_mode(modifier)


class OBJECT_OT_stop_motion_sculpt_multiples(Multiples):
    bl_idname = "object.stop_motion_sculpt_multiples"
    bl_label = "Sculpt Multiples"
    """Enter Sculpt Mode"""

    def set_mode(self, modifier):
        modes.set_sculpt_mode(modifier)


class OBJECT_OT_stop_motion_exit_multiples(bpy.types.Operator):
    """Back to boring old singles"""
    bl_idname = "object.stop_motion_exit_multiples"
    bl_label = "Exit Multiples"
    bl_options = {'REGISTER',}

    @classmethod
    def poll(cls, context):
        return context.scene.multiple_stop_motion_settings.editing

    def execute(self, context):
        scene = context.scene
        stopmo = bpy.data.objects[scene.multiple_stop_motion_settings.stopmo_object]
        modes.set_object_mode(Modifier(stopmo))
        stopmo.select_set(True)
        context.view_layer.objects.active = stopmo
        bpy.data.collections.remove(collection=bpy.data.collections[COLLECTION_NAME])
        if scene.multiple_stop_motion_settings.restore_onionskins:
            stopmo.onion_skin_settings.enable = True
        scene.multiple_stop_motion_settings.restore_onionskins = False
        scene.multiple_stop_motion_settings.editing = False
        scene.multiple_stop_motion_settings.stopmo_object = ""
        return {'FINISHED'}


class OBJECT_OT_stop_motion_multi_materials(bpy.types.Operator):
    bl_idname = "object.stop_motion_material_multiples"
    bl_label = "Assign Materials to multiple stop motion frames"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if not ob:
            cls.poll_message_set("No Active Object")
            return False
        if not Modifier(ob) and not context.scene.multiple_stop_motion_settings.editing:
            cls.poll_message_set(f"{ob.name} Not Initialized")
            return False
        return True

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        print("here")
        layout = self.layout


        ob = context.object

        space = context.space_data

        if ob:
            is_sortable = len(ob.material_slots) > 1
            rows = 5 if is_sortable else 3


            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")
            col.operator("object.material_slot_remove", icon='REMOVE', text="")

            col.separator()

            col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        row = layout.row()

        if ob:
            row.template_ID(ob, "active_material", new="material.new")

            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                if ob.type != 'FONT':
                    row.operator("object.material_slot_select", text="Select")
                    row.operator("object.material_slot_deselect", text="Deselect")


    def execute(self, context):
        ob = context.object
        if context.scene.multiple_stop_motion_settings.editing:
            targets = (tar for tar in context.selected_objects if tar is not ob)
            source = ob
        else:
            modifier = Modifier(ob)
            targets = modifier.selected_keyframes_objects()
            source = modifier.get_object()
        for target in targets:
            for idx, material in enumerate(source.data.materials):
                try:
                    target.data.materials[idx] = material
                except IndexError:
                    target.data.materials.append(material)

        return {'FINISHED'}


class StopMotionMultiplesSettings(bpy.types.PropertyGroup):
    """Multiples Editing Memory, stored on the Scene"""

    editing: bpy.props.BoolProperty(default=False, name="Editing Multiples")
    stopmo_object: bpy.props.StringProperty(default="", name="Stop Motion Object")
    restore_onionskins: bpy.props.BoolProperty(default=False, name="Restore Onion Skins")


def register():
    bpy.utils.register_class(StopMotionMultiplesSettings)
    bpy.types.Scene.multiple_stop_motion_settings = bpy.props.PointerProperty(
        type = StopMotionMultiplesSettings, name="Multiple Stop Motion Settings"
        )
    bpy.utils.register_class(OBJECT_OT_stop_motion_edit_multiples)
    bpy.utils.register_class(OBJECT_OT_stop_motion_sculpt_multiples)
    bpy.utils.register_class(OBJECT_OT_stop_motion_exit_multiples)
    bpy.utils.register_class(OBJECT_OT_stop_motion_multi_materials)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_stop_motion_edit_multiples)
    bpy.utils.unregister_class(OBJECT_OT_stop_motion_sculpt_multiples)
    bpy.utils.unregister_class(OBJECT_OT_stop_motion_exit_multiples)
    bpy.utils.unregister_class(OBJECT_OT_stop_motion_multi_materials)
    del bpy.types.Scene.multiple_stop_motion_settings
    bpy.utils.unregister_class(StopMotionMultiplesSettings)

if __name__ == "__main__":
    register()
