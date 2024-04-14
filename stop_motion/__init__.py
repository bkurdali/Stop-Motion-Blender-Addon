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
    importlib.reload(animation)
    importlib.reload(ui)
    importlib.reload(modes)
    importlib.reload(obj_io)
    importlib.reload(onion_skins)
    importlib.reload(preferences)
else:
    from . import animation
    from . import ui
    from . import modes
    from . import obj_io
    from . import onion_skins
    from . import preferences

import bpy

bl_info = {
    "name": "Stop Motion",
    "author": "Bassam Kurdali",
    "version": (0, 9, 7),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar",
    "description": "Turns Blender into a Virtual Stop Motion Studio",
    "warning": "Beta, Expect bugs and changes",
    "doc_url": "https://wiki.urchn.org/wiki/Stopmotion",
    "tracker_url": "https://github.com/bkurdali/Stop-Motion-Blender-Addon",
    "category": "Animation",
}

"""
TODO

- Workspace Niceties (Beginner Friendly)
- Streamline editing in text editor on export?
- Error handling
- Join Merge stop motions

- Tests
"""


# This allows you to right click on a button and link to documentation
def stop_motion_manual_map():
    url_manual_prefix = "https://docs.blender.org/manual/en/latest/"
    url_manual_mapping = (
        ("bpy.ops.mesh.add_object", "scene_layout/object/types.html"),
    )
    return url_manual_prefix, url_manual_mapping


def register():
    preferences.register()
    modes.register()
    animation.register()
    obj_io.register()
    onion_skins.register()
    ui.register()
    bpy.utils.register_manual_map(stop_motion_manual_map)


def unregister():
    bpy.utils.unregister_manual_map(stop_motion_manual_map)
    ui.unregister()
    onion_skins.unregister()
    obj_io.unregister()
    animation.unregister()
    modes.unregister()
    preferences.unregister()


if __name__ == "__main__":
    register()
    
