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

if "bpy" in locals():
    import importlib
    importlib.reload(modifier_data)
else:
    from . import modifier_data

import bpy
from .modifier_data import Modifier


"""
Experimental UI for overriding materials in Stop Motion branch.

Don't assume anything, that way we can deal with old files without any versioning
UNLESS UI becomes cumbersome

Two possible states:
1- no override: material comes from object in the frames collection
2- override: use a geometry nodes addon to set material

In the case of 1 we just need to update the material slot data on frame change in edit mode/other non object modes,
then the user can do their thing

In the case of 2 we need to add (if it doesn't exist a materializer addon) (initialize override)

Assigning materials has to be done through "own interface" - replicate materials slot interface. 




UI:
 Material popover

 - display active material slot of linked object
 - edit frame / assign frame

 - override
"""


def sync(source_object, target_object):
    """Copy Material Slot and Active Material"""
    for index, slot in enumerate(source_object.material_slots):
        try:
            target_object.material_slots[index].material = slot.material
        except IndexError:
            target_object.data.materials.append(slot.material)
        target_object.material_slots[index].link = slot.link



def assign(data, material, index=None):
    """Assign a material to a stop_motion_object and to it's frame source"""
    if index is not None and len(data.materials > index):
        data.materials[index] = material # If a slot is required and available, use it
        return
    data.materials.append(material)


class MATERIAL_OT_stopmotion_material_add(bpy.types.Operator):
    bl_idname = "material.stopmotion_material_add"
    bl_label = "Add stop motion material"
    bl_options = {'REGISTER', 'UNDO'}

    material: bpy.props.EnumProperty()
    index: bpy.props.IntProperty()

    def execute(self, context):
        stop_motion_object = context.object
        modifier = Modifier(stop_motion_object)
        target_object = modifier.object
        stop_motion_object.data = target_object.data
        assign(stop_motion_object.data, self.material, self.index)


class MATERIAL_OT_stopmotion_material_new(bpy.types.Operator):
    pass


class MATERIAL_OT_stopmotion_slot_add(bpy.types.Operator):
    pass


class MATERIAL_OT_stopmotion_slot_del(bpy.types.Operator):
    pass


class MATERIAL_OT_stopmotion_push(bpy.types.Operator):
    pass


class MATERIAL_OT_stopmotion_pull(bpy.types.Operator):
    pass
