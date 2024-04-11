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
    importlib.reload(version)
else:
    from . import version

import bpy

MODNAME = "StopMotion"
COLNAME = "StopMotion Sources"

# Data  Helpers


class Modifier():
    """ Convenience Stop Motion Modifier Access Class """

    name = MODNAME

    def __init__(self, obj):
        self.obj = obj
        if not obj:
            self.modifier = None
        else:
            self.modifier = obj.modifiers.get(MODNAME)
        if self.modifier:
            # Hopefully we won't use these outside the class
            self.__index__ = self.__get_input_label__("Instance Index")
            self.__collection__ = self.__get_input_label__("Collection")

            # Handy for e.g. < row.prop(m.modifier, m.index_prop) >
            self.index_prop = f'["{self.__index__}"]'
            self.collection_prop = f'["{self.__collection__}"]'

    def __bool__(self):
        """ We can use e.g. < is Modifier(obj) > in poll functions """
        return True if self.modifier else False

    def __get_input_label__(self, input):
        return self.modifier.node_group.interface.items_tree[input].identifier

    @property
    def index(self):
       return self.modifier[self.__index__]

    @index.setter
    def index(self, value):
        self.modifier[self.__index__] = value

    @property
    def collection(self):
        if not self.modifier:
            return None
        return self.modifier[self.__collection__]

    @collection.setter
    def collection(self, value):
        if not self.modifier:
            return
        self.modifier[self.__collection__] = value

    def get_fcurve(self):
        action = self.modifier.id_data.animation_data.action
        fcurves = (
            f for f in action.fcurves
            if f.data_path == f'modifiers["{self.modifier.name}"]["{self.__index__}"]' and f.array_index == 0
            )
        for fcurve in fcurves:
            return fcurve

    def keyframe_index(self, context):
        """ Insert a Keyframe at the current frame on the index prop """

        self.modifier.keyframe_insert(f'["{self.__index__}"]')

        # Now make sure it is constant
        fcurve = self.get_fcurve()
        if not fcurve:
            return # TODO error if no keyframe inserted
        keyframes = (
            k for k in fcurve.keyframe_points
            if abs(k.co[0] - context.scene.frame_current) <= .001
            )
        for keyframe in keyframes:
            keyframe.interpolation = 'CONSTANT'

    def future_keys(self, context):
        fcurve = self.get_fcurve()
        if not fcurve:
            return False # Technically this should be an error
        frame = context.scene.frame_current
        for keyframe in (k.co[0] for k in fcurve.keyframe_points if k.co[0] > frame):
            return True
        return False

    def object_name(self, index=None):
        """Return properly indexed object frame name"""
        if index is None:
            index = self.index
        # Might adjust formatting later to minimize collisions?
        return version.frame_name(index, self.obj)

    def get_object(self, index=None):
        name = self.object_name(index)
        collection = self.collection
        return collection.objects[name]

    def hide_viewport(self):
        self.modifier.show_viewport = False

    def reveal_viewport(self):
        self.modifier.show_viewport = True


class StopMotionOperator(bpy.types.Operator):
    """Wrapper for operators that need Modifier"""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if not ob:
            cls.poll_message_set("No Active Object")
            return False
        if not Modifier(ob):
            cls.poll_message_set(f"{ob.name} Not Initialized")
            return False
        return True

