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
    importlib.reload(update_handler)
    importlib.reload(modifier_data)
    importlib.reload(json_nodes)
else:
    from . import update_handler
    from . import modifier_data
    from . import json_nodes

import bpy
import os
from .modifier_data import Modifier, StopMotionOperator


def collection_name(source):
    return f"STPMO_onion_{source.name}"


def create_onion(source, offset):
    """ Create an onion skin object """
    # get the onion collection
    name = collection_name(source)
    collections = bpy.data.collections
    collection = collections.get(name, collections.new(name))
    collection.use_fake_user = True
    collection.use_select = False
    collection.show_render = False
    # Create the object
    name = f"STPMO_onion{'+' if offset >= 0 else '-'}_{offset:02}_{source.name}"
    objects = bpy.data.objects
    onion_object = objects.get(name, objects.new(name=name, object_data=source.data))
    onion_object.use_select = False
    onion_object.show_render = False
    # put it in the collection
    collection.objects.link(onion_object)
    # Create the material
    name = f"STPMO_onion_{'+' if offset >= 0 else '-'}_mat"
    materials = bpy.data.materials
    material = materials.get(name, materials.new(name))
    # add the modifiers
    for name, json_path, modname in (
            ("MeshKey", "modifier.json", Modifier.name),
            ("Materialize", "materializer.json", "Materializer")):
        node_group = json_nodes.read_node(
            name, os.path.join(os.path.dirname(__file__), json_path))
        modifier = onion_object.modifiers.new(modname, 'NODES')
        modifier.node_group = node_group
    # Assign material to second modifier
    modifier.material = material # pseudocode won't work
    # Copy modifier settings from source
    target_modifier = Modifier(source)
    my_modifier = Modifier(onion_object)
    my_modifier.collection = target_modifier.collection
    my_modifier.index = target_modifier.index + offset

    # Adjust object viewport properties to match material
    # do the nla of the action, offset it by offset
    return onion_object


def delete_onion(source, offset):
    return


class OBJECT_OT_stopmotion_onion_skins(StopMotionOperator):
    """Adjust number and offset of onion skins"""
    bl_idname = "object.stopmotion_onion_skins"
    bl_label = "Onion Skinning"

    future_frames: bpy.props.IntProperty(
        name="Future Frames", default=0, min=0, max=10)

    past_frames: bpy.props.IntProperty(
        name="Past Frames", default=0, min=0, max=10)

    offset: bpy.props.IntProperty(name="Offset", default=2, min=1)

    def execute(self, context):
        stop_motion_object = context.object
        modifier = Modifier(stop_motion_object)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_OT_stopmotion_onion_skins)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_stopmotion_onion_skins)
