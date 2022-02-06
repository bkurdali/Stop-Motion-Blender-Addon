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

if "bpy" in locals():
    import importlib
    importlib.reload(json_nodes)
    importlib.reload(modifier_data)
    importlib.reload(modes)
else:
    from . import json_nodes
    from . import modifier_data
    from . import modes

import bpy
import os
from modifier_data import Modifier


class StopMotionOperator(bpy.types.Operator):
    """ Save Typing some Things """
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object and Modifier(context.object)


class OBJECT_OT_add_stop_motion(bpy.types.Operator):
    """Create a new stop motion Object with an initial keyframe"""
    bl_idname = "object.add_stop_motion"
    bl_label = "Add Stop Motion Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and not Modifier(obj)

    def execute(self, context):

        scene = context.scene
        stop_motion_object = context.object

        # Create Source Collection
        stop_motion_collection = bpy.data.collections.new(
            name=Modifier.collection_name)
        # Instead of linking fake user to prevent accidents
        stop_motion_collection.use_fake_user = True
        stop_motion_collection.hide_render = True
        stop_motion_collection.hide_viewport = True

        # Create and Populate Modifiers
        for name, json_path, modname in (
                ("MeshKey", "modifier.json", MODNAME),
                ("Realize", "realizer.json", "Realizer")):
            node_group = json_nodes.read_node(
                name, os.path.join(os.path.dirname(__file__), json_path))
            modifier = stop_motion_object.modifiers.new(modname, 'NODES')
            modifier.node_group = node_group
        modifier.show_viewport = modifier.show_in_editmode = False # Don't realize by default

        modifier = Modifier(stop_motion_object) # for convenient access
        modifier.collection = stop_motion_collection
        modifier.index = 0
        modifier.keyframe_index(context)
        modifier.modifier.show_in_editmode = False

        first_frame = stop_motion_object.copy()
        first_frame.name = modifier.object_name()
        old_collections = [
            c for c in bpy.data.collections if first_frame.name in c]
        for c in old_collections:
            c.objects.unlink(first_frame)
        stop_motion_collection.objects.link(first_frame)

        return {'FINISHED'}

# Animation Operators


def insert_keyframe(context, source_data, use_copy=False):
    """ Appends a keyshape at end; doesn't disrupt the alphabetical order """
    obj = context.object
    if not obj:
        return
    modifier = Modifier(obj)
    if not modifier:
        return
    mode = obj.mode
    modes.set_object(mode)

    collection = modifier.collection
    index = len(collection.objects)
    newest = modifier.object_name(index=index)

    if not source_data:
        source_data = collection.objects[int_to_str(modifier.index)].data
        use_copy = True # Always copy the current shape if keyframing it

    shape_data = source_data.copy() if use_copy else source_data
    shape_ob = bpy.data.objects.new(name=newest, object_data=shape_data)

    collection.objects.link(shape_ob)
    modifier.index = index
    modifier.keyframe_index(context)

    obj.data = shape_ob.data
    modes.restore(mode, obj)


class OBJECT_OT_keyframe_stop_motion(StopMotionOperator):
    """Add a key drawing/ frame, optionally from selection"""
    bl_idname = "object.keyframe_stop_motion"
    bl_label = "New Keyframe"

    use_copy: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        stop_motion_object = context.object
        possible_sources = (
            o for o in context.selected_objects
            if o is not stop_motion_object and o.type == 'MESH')
        for source in possible_sources:
            insert_keyframe(context, source.data, use_copy=self.use_copy)
            return {'FINISHED'} # We only care about 1 selected object
        insert_keyframe(context, None, use_copy=True)
        return {'FINISHED'}


class OBJECT_OT_Join_keyframe_stop_motion(StopMotionOperator):
    """Join Selected Meshes into a new keyframe"""
    bl_idname = "object.join_stop_motion"
    bl_label = "Join Keyframe"

    @classmethod
    def poll(cls, context):
        return (
            StopMotionOperator.poll(context) and context.mode == 'OBJECT'
            and len(context.selected_objects) > 1)

    def execute(self, context):
        stop_motion_object = context.object
        insert_keyframe(context, None, use_copy=True)
        mode = stop_motion_object.mode
        modes.set_object(mode)
        bpy.ops.object.join()
        modes.restore(mode, stop_motion_object)
        return {'FINISHED'}


class SCREEN_OT_next_or_add_key(bpy.types.Operator):
    """Goto next available keyframe, add one if unavailable"""
    bl_idname = "screen.next_or_keyframe_stop_motion"
    bl_label = "Next/Add Next Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    frame_offset: bpy.props.IntProperty(default=0, min=0, soft_min=1, max=100)
    use_copy: bpy.props.BoolProperty(default=True)

    first_run = True

    def fallback(self):
        result = bpy.ops.screen.keyframe_jump()
        if result == {'CANCELLED'}:
            self.report(
                {'WARNING'}, "No more keyframes to jump in this direction")
        return result

    def execute(self, context):

        modifier = Modifier(context.object)
        if not modifier or modifier.future_keys(context):
            return self.fallback()

        # Set the offset to addon preferences on first run
        if SCREEN_OT_next_or_add_key.first_run:
            SCREEN_OT_next_or_add_key.first_run = False
            preferences = context.preferences.addons[__package__].preferences
            self.frame_offset = preferences.frame_offset

        if self.frame_offset == 0:
            return self.fallback()

        context.scene.frame_set(context.scene.frame_current + self.frame_offset)
        return bpy.ops.object.keyframe_stop_motion(use_copy=self.use_copy)

# Registration


def register():
    bpy.utils.register_class(OBJECT_OT_add_stop_motion) # Create and Initialize
    bpy.utils.register_class(OBJECT_OT_keyframe_stop_motion) # Insert New Key
    bpy.utils.register_class(SCREEN_OT_next_or_add_key)
    bpy.utils.register_class(OBJECT_OT_Join_keyframe_stop_motion)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_stop_motion)
    bpy.utils.unregister_class(SCREEN_OT_next_or_add_key)
    bpy.utils.unregister_class(OBJECT_OT_keyframe_stop_motion)
    bpy.utils.unregister_class(OBJECT_OT_Join_keyframe_stop_motion)

if __name__ == "__main__":
    register()
