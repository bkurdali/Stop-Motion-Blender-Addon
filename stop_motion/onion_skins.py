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


class OnionCollection():
    """Wrapper for Onion Skin Collection"""

    props = {
        "use_fake_user": True, "hide_select": True, "hide_render": True,}

    def __init__(self.source):
        self.source = source
        self.set_name()
        collections = bpy.data.collections
        self.collection = collections.get(
            self.name, collections.new(self.name))
        self.set_properties()
        return collection

    def set_name(self):
        self.name = f"STPMO_onion_{self.source.name}"
        return self.name

    def set_properties(self, props=None):
        if not props:
            props = self.props
        for prop, value in props.items():
            setattr(self.collection, prop, value)

    def link(self, obj):
        if obj.name not in self.collection.objects:
            self.collection.objects.link(obj)


class OnionMaterial():
    """Wrapper for Onion Skin Material"""

    props = {
        "use_nodes": True, "blend_method": 'BLEND', "shadow_method": 'NONE',
        "use_backface_culling": True, "roughness": 1, "use_fake_user": True
        }

    diffuse_color = ([1 , 0, 0, .2], [0, 1, 0, .2])

    def __init__(self, offset, index)
        self.forward = offset > 0
        self.index = index
        name = self.set_name()
        materials = bpy.data.materials
        self.material = materials.get(name)
        if self.material:
            return # Material exists, we're done here
        # Create and setup new material
        self.material = materials.new(name)
        self.set_properties()
        self.set_node_tree()

    def set_node_tree(self):
        material = self.material
        # get rid of any helpful defaults (e.g. principled shader node)
        for node in material.node_tree.nodes:
            if node.type != 'OUTPUT_MATERIAL':
                material.node_tree.nodes.remove(node)
        # create group node
        group_node = material.node_tree.nodes.new(type='ShaderNodeGroup')
        filepath = os.path.join(os.path.dirname(__file__), "material.json")
        onion_group = json_nodes.read_node("Oniony", filepath)
        group_node.node_tree = onion_group
        # link the group to the material output
        link = node_tree.links.new(
            node_from="", node_to="", socket_from="", socket_to="")

    def set_properties(self, props=None):
        if not props:
            props = self.props
        for prop, value in self.props.items():
            setattr(self.material, prop, value)
        self.material.diffuse_color = self.diffuse_color[self.forward]

    def set_opacity(self, opacity):
        self.material.diffuse_color[3] = opacity

    def set_name(self):
        self.name = f"STPMO_onion_{'+' if self.forward else '-'}_{self.index:02}"
        return self.name


class OnionSkin():
    """Creates or gets an onion skin"""

    def set_name(self.forward, self.source, self.index):
        return f"STPMO_onion{'+' if self.forward else '-'}_{self.index:02}_{self.source.name}"

    def create_onion(source, offset, index):
        """ Create an onion skin object """
        forward = offset > 0 # What direction am I in?

        onion_collection = OnionCollection(source)
        # Create the object
        name = object_name(forward, source, index)
        objects = bpy.data.objects
        onion_object = objects.get(name)
        if onion_object:
            onion_collection.link(onion_object)
            return onion_object
        onion_object = objects.new(name=name, object_data=source.data))
        onion_collection.link(onion_object)

        onion_object.hide_select = onion_object.hide_render = True

        # Create the material
        material = OnionMaterial(offset, index)

        # add the modifiers
        for name, json_path, modname in (
                ("MeshKey", "modifier.json", Modifier.name),
                ("Materialize", "materializer.json", "Materializer")):
            node_group = json_nodes.read_node(
                name, os.path.join(os.path.dirname(__file__), json_path))
            modifier = onion_object.modifiers.new(modname, 'NODES')
            modifier.node_group = node_group
        # Assign material to second modifier
        identifier = modifier.node_group.inputs['Material'].identifier
        modifier[identifier] = material
        # Copy modifier settings from source
        target_modifier = Modifier(source)
        my_modifier = Modifier(onion_object)
        my_modifier.collection = target_modifier.collection
        my_modifier.index = target_modifier.index + offset

        # Adjust object viewport properties to match material

        # do the nla of the action, offset it by offset
        action = source.animation_data.action
        animation_data = onion_object.animation_data_create()
        nla_track = animation_data.nla_tracks.new()
        strip = nla_track.strips.new(
            action.name, action.frame_range[0] + offset, action)

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
