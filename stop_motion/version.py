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
import addon_utils

SUB = 0
bl_info = addon_utils.modules().mapping['stop_motion'].bl_info
MAJOR, MINOR, SUB = bl_info['version']
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

def prefix():
    return f"{NAME}_{FRAME}_"


def frame_name(index, obj):
    return f"{prefix()}{obj.name}_{index:04}"


def collection_name(obj):
    return f"{prefix()}{obj.name}"


def onion_skin_instance(forward, index):
    return f"{onion_prefix()}{'+' if forward else '-'}_{index:02}"


def onion_skin_name(forward, index, source_id):
    return f"{onion_skin_instance(forward, index)}_{source_id}"


def onion_skins_name(source_id):
    """ onion skin collection name """
    return f"{onion_prefix()}{source_id}"


onion_skin_material_name = onion_skin_instance


def modifier_name():
    return bl_info['name'].replace(" ","")

# ID fixing functions (object names but will be replaced by hashes)

# TODO updating names
# TODO split detecting bad id into own function


def update_frame_id(new_id, old_frame_name):
    old_id = old_frame_name.replace(prefix(),"").split('_')[-2]
    return old_Frame_name.replace(old_id, new_id)


def update_collection_id(new_id, old_collection_name):
    old_id = old_collection_name.replace(prefix(),"")
    return old_collection_name.replace(old_id, new_id)


def get_onion_id_prefix_from_name(onion_name):
    components = onion_name.replace(prefix(), "")split('_')
    id_prefix = f"{prefix()}{'_'.join(components[0], components[1])}_"
    return id_prefix


def update_onion_skin_frames_id(new_id, old_onion_skin_name):
    id_prefix = get_onion_id_prefix_from_name(old_onion_skin_name)
    old_id = old_onion_skin_name.replace(id_prefix,"")
    return old_onion_skin_name.replace(old_id, new_id)


def update_onion_skin_collection_id(new_id, old_onion_skins_name):
    return f"{onion_prefix()}{new_id}"






