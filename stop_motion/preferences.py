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

import bpy

class StopMotionPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    frame_offset: bpy.props.IntProperty(
        name="Frame Offset",
        description="Use up arrow to key after last frame: 2 for twos, 0 to disable",
        default=2)

    tab_for_pie_menu: bpy.props.BoolProperty(
        name="Tab for Pie Menu",
        description="Need to use this instead of the Keymap Preference",
        default=False
        )

    use_smooth_groups: bpy.props.BoolProperty(
        name="Use Smooth Groups",
        default=False)

    use_normals: bpy.props.BoolProperty(
        name="Use Normals",
        default=False)

    use_uvs: bpy.props.BoolProperty(
        name="Use UVs",
        default=False)


    use_materials:bpy.props.BoolProperty(
        name="Use Materials",
        default=False)

    use_vertex_groups:bpy.props.BoolProperty(
        name="Use Vertex Groups",
        default=False)

    use_colors:bpy.props.BoolProperty(
        name="Use Colors",
        default=False)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Stop Motion Preferences")
        layout.prop(self, "frame_offset")
        layout.prop(self, "tab_for_pie_menu")
        layout.separator()
        layout.label(text="OBJ IO Preferences")
        layout.prop(self, "use_normals")
        layout.prop(self, "use_uvs")
        layout.prop(self, "use_materials")
        layout.prop(self, "use_vertex_groups")
        layout.prop(self, "use_smooth_groups")
        layout.prop(self, "use_colors")


def register():
    bpy.utils.register_class(StopMotionPreferences)


def unregister():
    bpy.utils.unregister_class(StopMotionPreferences)
