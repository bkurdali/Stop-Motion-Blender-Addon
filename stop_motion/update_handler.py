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
    importlib.reload(modifier_data)
else:
    from . import modifier_data
    from . import materials
import bpy
from .modifier_data import Modifier


def stop_motion_data(scene):
    """Update object data as quickly as possible in non object modes"""
    stop_motion_object = bpy.context.object
    mode = stop_motion_object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    source_object = Modifier(stop_motion_object).get_object()
    stop_motion_object.data = source_object.data
    materials.sync(source_object, stop_motion_object)
    bpy.ops.object.mode_set(mode=mode)


def handler_loop(func):
    def wrapper():
        for handler in bpy.app.handlers.frame_change_post:
             if stop_motion_data.__name__ == handler.__name__:
                 return func(handler)
    return wrapper


@handler_loop
def is_running(handler):
    """Check if an updater is running"""
    return True


@handler_loop
def remove(handler):
    """Remove updater"""
    bpy.app.handlers.frame_change_post.remove(handler)


def add():
    if not is_running():
        bpy.app.handlers.frame_change_post.append(stop_motion_data)
