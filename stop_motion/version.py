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

"""
Version Information
Central class to provide version tagging, perhaps some kind of do_versions
down the road if I can be bothered
"""

MAJOR = 0
MINOR = 9
SUB = 3
NAME = "STPMO"

ONION = "onion"
MAIN_OBJECT = "main"

FRAME = "frame"

def get():
    return (MAJOR, MINOR, SUB)


def onion_prefix():
    return f"{NAME}_{ONION}_"


def tag():
    return (NAME, {'major': MAJOR, 'minor':MINOR})


def onion_tag(item):
    """Leave breadcrumbs"""
    item_tag = tag()
    item_tag[1]['type'] = ONION
    item[item_tag[0]] = item_tag[1]


def main_tag(item):
    """Leave breadcrumbs"""
    item_tag = tag()
    item_tag[1]['type'] = MAIN_OBJECT
    item_tag[1]['name'] = item.name
    item[item_tag[0]] = item_tag[1]


def frame_name(index, obj):
    return f"{NAME}_{FRAME}_{obj.name}_{index:04}"


def collection_name(obj):
    return f"{NAME}_{FRAME}s_{obj.name}"
