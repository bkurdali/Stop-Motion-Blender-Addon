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
    importlib.reload(version)
    importlib.reload(modes)
else:
    from . import update_handler
    from . import modifier_data
    from . import json_nodes
    from . import version
    from . import modes

import bpy
import os
from .modifier_data import Modifier, StopMotionOperator


class OnionCollection():
    """Wrapper for Onion Skin Collection"""

    props = {
        "use_fake_user": True, "hide_select": True, "hide_render": True,}

    def __init__(self,scene, source):
        self.source = source
        self.scene = scene
        self.set_name()
        collections = bpy.data.collections
        self.collection = collections.get(self.name)
        if self.collection:
            self.scene_attach()
            return
        self.collection = collections.new(self.name)
        self.scene_attach()
        version.onion_tag(self.collection)
        self.set_properties()

    def set_name(self):
        self.name = f"{version.onion_prefix()}{self.source.name}"

    def set_properties(self, props=None):
        if not props:
            props = self.props
        for prop, value in props.items():
            setattr(self.collection, prop, value)

    def link(self, obj):
        if obj and obj.name not in self.collection.objects:
            self.collection.objects.link(obj)

    def unlink(self, obj):
        if obj and obj.name in self.collection.objects:
            self.collection.objects.unlink(obj)

    def scene_attach(self):
        if self.collection.name in self.scene.collection.children:
            return
        self.scene.collection.children.link(self.collection)

    def scene_detach(self):
        if self.collection.name not in self.scene.collection.children:
            return
        self.scene.collection.children.unlink(self.collection)

class OnionMaterial():
    """Wrapper for Onion Skin Material"""

    props = {
        "use_nodes": True, "blend_method": 'BLEND', "shadow_method": 'NONE',
        "use_backface_culling": True, "roughness": 1, "use_fake_user": True
        }

    def __init__(self, offset, index, color, opacity):

        self.forward = offset > 0
        self.index = index
        self.set_name()
        materials = bpy.data.materials
        self.material = materials.get(self.name)
        if self.material:
            self.inputs = self.material.node_tree.nodes['Group'].inputs
            self.color = color
            self.opacity = opacity
            return # Material exists, we're done here
        # Create and setup new material
        self.material = materials.new(self.name)
        version.onion_tag(self.material)
        self.set_properties()
        self.set_node_tree()
        self.inputs = self.material.node_tree.nodes['Group'].inputs
        self.color = color
        self.opacity = opacity

    def set_node_tree(self):
        material = self.material
        # get rid of any helpful defaults (e.g. principled shader node)
        for node in material.node_tree.nodes:
            if node.type != 'OUTPUT_MATERIAL':
                material.node_tree.nodes.remove(node)
        # create group node
        group_node = material.node_tree.nodes.new(type='ShaderNodeGroup')
        filepath = os.path.join(os.path.dirname(__file__), "material.json")
        onion_group = json_nodes.read_node("Oniony", filepath, tree_type="ShaderNodeTree")
        group_node.node_tree = onion_group
        # link the group to the material output
        link = material. node_tree.links.new(
            group_node.outputs['Shader'],
            material.node_tree.nodes['Material Output'].inputs['Surface'])
        self.inputs = group_node.inputs

    def set_properties(self, props=None):
        if not props:
            props = self.props
        for prop, value in self.props.items():
            setattr(self.material, prop, value)


    @property
    def opacity(self):
        return self.inputs['Opacity'].default_value

    @opacity.setter
    def opacity(self, opacity):
        self.material.diffuse_color[3] = opacity
        self.inputs['Opacity'].default_value = opacity

    @property
    def color(self):
        return [self.inputs['Color'].default_value[i] for i in range(3)]

    @color.setter
    def color(self, color):
        """Set RGB to a 3 float array"""
        for i, value in enumerate(color):
            self.inputs['Color'].default_value[i] = value
            self.material.diffuse_color[i] = value

    def set_name(self):
        self.name = f"{version.onion_prefix()}{'+' if self.forward else '-'}_{self.index:02}"


class OnionSkin():
    """Creates or gets an onion skin"""

    props = {"hide_select": True, "hide_render": True, "display": {"show_shadows": False}}

    def set_name(self):
        self.name = f"{version.onion_prefix()}{'+' if self.forward else '-'}_{self.index:02}_{self.source.name}"

    def __init__(self, scene, source, offset, index, color, opacity, create):
        """ Create an onion skin object """
        self.forward = offset > 0
        self.source = source
        self.offset = offset
        self.index = index
        self.color = color
        self.opacity = opacity

        self.collection = OnionCollection(scene, source)
        # Create the object
        self.set_name()
        objects = bpy.data.objects
        self.obj = objects.get(self.name)
        if not create:
            if self.obj:
                self.delete()
            return
        if not self.obj:
            self.obj = objects.new(name=self.name, object_data=source.data)
            version.onion_tag(self.obj)
        self.collection.link(self.obj)
        self.modifier()
        self.set_properties()
        self.animation()

    def __bool__(self):
        return True if self.obj else False

    def modifier(self):
        # Create the material
        self.material = OnionMaterial(
            self.offset, self.index, self.color, self.opacity)
        if Modifier(self.obj):
            return
        # add the modifiers
        for name, json_path, modname in (
                ("MeshKey", "modifier.json", Modifier.name),
                ("Materialize", "materializer.json", "Materializer")):
            node_group = json_nodes.read_node(
                name, os.path.join(os.path.dirname(__file__), json_path))
            modifier = self.obj.modifiers.new(modname, 'NODES')
            modifier.node_group = node_group
        # Assign material to second modifier
        identifier = modifier.node_group.inputs['Material'].identifier
        modifier[identifier] = self.material.material
        # Copy modifier settings from source
        target_modifier = Modifier(self.source)
        my_modifier = Modifier(self.obj)
        my_modifier.collection = target_modifier.collection
        my_modifier.index = target_modifier.index + self.offset

        # Adjust object viewport properties to match material

    def animation(self):
        # do the nla of the action, offset it by offset
        action = self.source.animation_data.action
        self.obj.animation_data_clear()
        animation_data = self.obj.animation_data_create()
        nla_track = animation_data.nla_tracks.new()
        strip = nla_track.strips.new(
            action.name, action.frame_range[0] - self.offset , action)

    def set_properties(self, props=None):
        if not props:
            props = self.props
        for prop, value in self.props.items():
            if type(value) is dict:
                sub_obj = getattr(self.obj, prop)
                for sub_prop, sub_value in value.items():
                    setattr(sub_obj, sub_prop, sub_value)
            else:
                setattr(self.obj, prop, value)
        for index, value in enumerate(self.color):
            self.obj.color[index] = value
        self.obj.color[3] = self.opacity

    def delete(self):
        self.collection.unlink(self.obj)


class OnionSkinManager():
    """handle onion skins for a given object"""

    maximum = 10

    def __init__(self,scene, stop_motion_object):
        self.stop_motion_object = stop_motion_object
        settings  = stop_motion_object.onion_skin_settings
        self.enable = settings.enable
        self.opacity = settings.opacity
        self.offset = settings.frame_offset
        self.count = (settings.before, settings.after)
        self.color = (settings.before_color, settings.after_color)
        self.scene = scene
        self.onion_skins_load()

    def __bool__(self):
        return True if any([items for items in self.objects]) else False

    def onion_skins_load(self):
        self.objects =[[],[]]
        for side, items in enumerate(self.objects):

            for index in range(self.maximum):
                create = self.enable and index < self.count[side]
                sign = -1 if side == 0 else 1
                # set proper time offset
                # set proper opacity offset
                opacity = self.opacity * (self.count[side] - index) / self.count[side]
                offset = sign * (self.offset + self.offset * index)
                onion_skin_object = OnionSkin(
                    self.scene,
                    self.stop_motion_object, offset ,
                    index, self.color[side], opacity, create)
                if onion_skin_object:
                    items.append(onion_skin_object)

    def refresh(self):
        for side in self.objects:
            for onion_skin_object in side:
                onion_skin_object.animation()

    def onion_skins_unload(self):
        for items in self.objects:
            for onion_skin in items:
                onion_skin.delete()
# Operators


def sync_onion_skins(scene, stop_motion_object):
    """Sync NLA strips for stop motion object"""
    # mode = stop_motion_object.mode
    # modes.set_object(mode)
    OnionSkinManager(scene, stop_motion_object).refresh()
    # modes.restore(mode, stop_motion_object)

class OBJECT_OT_sync_onion_skins(StopMotionOperator):
    """Re-sync Onion Skins on animation length change"""
    bl_idname = "object.sync_onion_skins"
    bl_label = "Syncronize Onion Skins"

    def execute(self, context):
        sync_onion_skins(context.scene, context.object)
        return {'FINISHED'}

# Properties


def onion_property_enable(self, context):
    stop_motion_object = context.object
    onion_skin_objects = OnionSkinManager(context.scene, stop_motion_object)


def onion_property_update(self, context):
    if not self.enable:
        return
    stop_motion_object = context.object
    onion_skin_objects = OnionSkinManager(context.scene, stop_motion_object)


class StopMotionOnionSkinSettings(bpy.types.PropertyGroup):
    """Onion Skin Settings, store per object"""

    enable: bpy.props.BoolProperty(
        name="Enable", options=set(), default=False, update=onion_property_enable)
    frame_offset: bpy.props.IntProperty(
        name="Frame Offset", description="Number of Frames between Onion Skins",
        options=set(), default=2, min=1, soft_max=5, max=20, update=onion_property_update)
    opacity: bpy.props.FloatProperty(
        name="Opacity", options=set(), default=0.2, min=.005, max=.8, update=onion_property_update)
    before: bpy.props.IntProperty(
        name="Skins Before", description="Number of Onion Skins before current frame",
        options=set(), default=1, min=1, soft_max=4,
        max=OnionSkinManager.maximum, update=onion_property_update)
    after: bpy.props.IntProperty(
        name="Skins After", description="Number of Onion Skins after current frame",
        options=set(), default=1, min=1, soft_max=4,
        max=OnionSkinManager.maximum, update=onion_property_update)
    before_color:bpy.props.FloatVectorProperty(
        name="Color Before", description="Onion Skin Color before current frame",
        options=set(), subtype='COLOR', default=(1.0,0.0,0.0),
        min=0.0, max=1.0, size=3, update=onion_property_update)
    after_color:bpy.props.FloatVectorProperty(
        name="Color After", description="Onion Skin Color after current frame",
        options=set(), subtype='COLOR', default=(0.0,1.0,0.2),
        min=0.0, max=1.0, size=3, update=onion_property_update)


def register():
    bpy.utils.register_class(StopMotionOnionSkinSettings)
    bpy.types.Object.onion_skin_settings = bpy.props.PointerProperty(
        type=StopMotionOnionSkinSettings, name="Onion Skin Settings"
        )
    bpy.utils.register_class(OBJECT_OT_sync_onion_skins)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_sync_onion_skins)
    del bpy.types.Object.onion_skin_settings
    bpy.utils.unregister_class(StopMotionOnionSkinSettings)
