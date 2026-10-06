# Copyright 2026 Ursula Kurdali / urchn.org
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
Utilities to copy data from a source to a target, used by multiple modules
"""

import bpy


def materials(source, target):
    """ Copy all the materials from a source to a target object"""
    for idx, material in enumerate(source.data.materials):
        try:
            target.data.materials[idx] = material
        except IndexError:
            target.data.materials.append(material)


def uvs(source, target):
    """ Copy UV layers from source to target but leave intact existing layers """
    pass
