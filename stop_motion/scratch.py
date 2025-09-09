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
else:
    pass

import bpy


def offset_points(points, delta):
    """ yield offset coordinates x, y(x + delta) from fcurve points"""
    for i, point in enumerate(points):
        yield point.co[0], points[i + delta].co[1]


def offset_action(action, target, data_path, delta):
    """ offset fcurve[data_path] from action into target action """
    points = offset_points(action.fcurves[data_path].keyframe_points, delta)
    for i, point in enumerate(points):
        target.fcurves[data_path].keyframe_points[i].co = point


def copy_offset(action, data_path, offset):
    """  """
    target = action.copy()
    offset_action(action, target, data_path, offset)
    return target


def update_offset(action, target, data_path, offset):
    """  """
    source_points = action.fcurves[data_path].keyframe_points
    target_points = target.fcurves[data_path].keyframe_points
    difference = len(source_points) - len(target_points)
    if difference > 0:
        target_points.add(difference)
    if difference < 0:
        for i in range(-difference):
            target_points.remove(target_points[-1])
    offset_action(action, target, data_path, offset)
