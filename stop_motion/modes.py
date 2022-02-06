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
Mode switching is tricky, so we need to wrap mode change operators

Since we rely on object data to edit/sculpt etc we need to copy it from
the modifier when going to sub-object modes
We need an update handler for sub-object modes since the data needs to update on
every frame
We need to disable the modifier in sub-object modes so that paint overlays
appear
"""

if "bpy" in locals():
    import importlib
    importlib.reload(update_handler)
    importlib.reload(modifier_data)
else:
    from . import update_handler
    from . import modifier_data

import bpy
from .modifier_data import Modifier, StopMotionOperator


def set_object(mode):
    if mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def restore(mode, obj):
    if mode != obj.mode:
        bpy.ops.object.mode_set(mode=mode)


class OBJECT_OT_stop_motion_mode(StopMotionOperator):
    """Switch Mode with corrected meshes """
    bl_idname = "object.stop_motion_mode"
    bl_label = "Stop Motion Mode"

    mode: bpy.props.EnumProperty(
        items = [
            ('OBJECT', 'Object Mode', 'OBJECT', 'OBJECT_DATAMODE', 0),
            ('EDIT', 'Edit Mode', 'EDIT', 'EDITMODE_HLT', 1),
            ('SCULPT', 'Sculpt Mode', 'SCULPT', 'SCULPTMODE_HLT', 2),
            ('VERTEX_PAINT', 'Vertex Paint Mode', 'VERTEX_PAINT', 'VPAINT_HLT', 3),
            ('WEIGHT_PAINT', 'Weight Paint Mode', 'WEIGHT_PAINT', 'MOD_VERTEX_WEIGHT', 4),
            ('TEXTURE_PAINT', 'Texture Paint Mode', 'TEXTURE_PAINT', 'TPAINT_HLT', 5)],
        default='OBJECT')

    toggle: bpy.props.BoolProperty(default=False)

    def execute(self, context):

        ob = context.object
        modifier = Modifier(ob)
        if modifier:
            collection = modifier.collection
            index = modifier.index

            # put the correct object_data in
            sources = sorted([o for o in collection.objects], key=lambda o:o.name)
            ob.data = sources[index].data

            if self.toggle and self.mode == ob.mode:
                self.mode = 'OBJECT'

            if self.mode == 'OBJECT':
                update_handler.remove()
                modifier.reveal_viewport()
            else:
                update_handler.add()
                modifier.hide_viewport()

        return bpy.ops.object.mode_set(mode=self.mode, toggle=self.toggle)


class OBJECT_OT_stop_motion_updater_toggle(bpy.types.Operator):
    """Start / Stop the Updater"""
    bl_idname = "object.stop_motion_updater_toggle"
    bl_label = "Toggle Updater"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        modifier = Modifier(obj)
        running = update_handler.is_running()
        if not modifier:
            return running
        object_mode = obj.mode == 'OBJECT'
        if object_mode:
            return running
        return not running

    def execute(self, context):
        modifier = Modifier(context.object)
        if update_handler.is_running():
            update_handler.remove()
            if modifier.modifier:
                modifier.reveal_viewport()
        else:
            update_handler.add()
            if modifier.modifier:
                modifier.hide_viewport()
        return {'FINISHED'}

# Registration


def register():
    bpy.utils.register_class(OBJECT_OT_stop_motion_mode) # Mode Change Wrapper
    bpy.utils.register_class(OBJECT_OT_stop_motion_updater_toggle)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_stop_motion_updater_toggle)
    bpy.utils.unregister_class(OBJECT_OT_stop_motion_mode)

if __name__ == "__main__":
    register()
