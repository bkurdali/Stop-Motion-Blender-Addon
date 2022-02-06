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
else:
    from . import update_handler
    from . import modifier_data

import bpy
from .modifier_data import Modifier

# Keymaps


class KeyMaps():

    settings = (
        (
            "Frames", 'EMPTY', "screen.next_or_keyframe_stop_motion",
            'UP_ARROW', {}, {}),
        (
            "3D View", 'VIEW_3D', "wm.call_menu_pie", 'D',{},
            {'name': 'VIEW3D_MT_PIE_StopMotion'}),
        (
            "Object Non-modal", 'EMPTY', "wm.call_menu_pie", 'TAB',
            {'ctrl': 1}, {'name': 'VIEW3D_MT_PIE_StopMotion_Mode'}),
        (
            "Object Non-modal", 'EMPTY', "object.stop_motion_mode",
            'TAB', {'ctrl': 0}, {'mode': 1, 'toggle': True})
    )

    @classmethod
    def map(cls, context):
        cls.keymaps = []
        preferences = context.preferences.addons[__package__].preferences
        use_tab_menu = preferences.tab_for_pie_menu
        kc = context.window_manager.keyconfigs.addon.keymaps
        for keymap_name, keymap_space, operator, key, mods, props in cls.settings:
            km = kc.get(keymap_name, kc.new(
                name=keymap_name,space_type=keymap_space))
            kmi = km.keymap_items.new(operator, key, 'PRESS')
            for prop, value in mods.items():
                setattr(kmi, prop, value)

            # Really Yucky but I don't know how else to do this
            if operator == "wm.call_menu_pie" and props.get('name') == 'VIEW3D_MT_PIE_StopMotion_Mode':
                kmi.ctrl = 0 if use_tab_menu else 1
            elif operator == "object.stop_motion_mode":
                kmi.ctrl = 1 if use_tab_menu else 0

            for prop, value in props.items():
                kmi.properties[prop] = value
            cls.keymaps.append((km, kmi))

    @classmethod
    def unmap(cls):
        if hasattr(cls, "keymaps"):
            for km, kmi in cls.keymaps:
                km.keymap_items.remove(kmi)
            cls.keymaps.clear()

# Draw Functions


def draw_first(context, layout, item_func):
    """Draw the first Button, just for the panel"""
    ob = context.object
    mod = Modifier(ob)
    row = item_func(layout)
    if not mod:
        row.operator(
            "object.add_stop_motion",
            text="", icon='PLUS')
        return

    icon = bpy.types.Object.bl_rna.properties["mode"].enum_items[ob.mode].icon
    row.operator_menu_enum(
        "object.stop_motion_mode", "mode",
        text="",
        icon=icon)


class Draw():

    def __init__(self, layout, item_func, operators):
        self.layout = layout
        self.item_func = item_func
        self.operators = operators

    def button(self, operator, text, icon, props):
        """ Draw a single Button """
        item = self.item_func(self.layout).operator(
            operator,
            text=text, icon=icon
            )
        for prop, value in props.items():
            setattr(item, prop, value)

    def buttons(self, context):
        """ All the Operator Buttons """
        # Operator idname, text, icon, props dict
        for operator, text, icon, props in self.operators:
            self.button(operator, text, icon, props)

# Panels


class StopMotionPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = ""
    bl_idname = "OBJECT_PT_Stopmotion"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "StopMo"


    main_operators = [
        (
            "object.keyframe_stop_motion", "", 'DECORATE_KEYFRAME',
            {"use_copy": True}),
        ("screen.next_or_keyframe_stop_motion", "", 'NEXT_KEYFRAME', {}),
        ("object.join_stop_motion", "", 'MOD_BOOLEAN', {}),
    ]
    obj_operators = [
        ("object.export_stop_motion_obj", "", 'CURRENT_FILE', {}),
        ("object.import_stop_motion_obj", "", 'FILE', {}),
    ]

    def new_row(self, layout):
        row = layout.row()
        row.ui_units_x = 200
        row.scale_x = 2
        return row

    def draw(self, context):
        flow = layout = self.layout
        layout.use_property_split = True

        ob = context.object

        flow = layout.split()

        col = flow.column()
        col.scale_y = 2

        draw_first(context, col, self.new_row)
        Draw(col, self.new_row, self.main_operators).buttons(context)
        drawer = Draw(col, self.new_row, self.obj_operators)
        drawer.buttons(context)
        running = update_handler.is_running()
        icon = 'PLAY' if not running else 'SNAP_FACE'
        drawer.button(
            operator="object.stop_motion_updater_toggle",
            text="", icon=icon, props={})

# Menus


class VIEW3D_MT_PIE_StopMotion(bpy.types.Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Select Mode"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        Draw(pie, lambda x:x, StopMotionPanel.main_operators).buttons(context)


class VIEW3D_MT_PIE_StopMotion_Mode(bpy.types.Menu):
    bl_label = "Select Mode"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        modifier = Modifier(context.object)
        if modifier:
            pie.operator_enum("object.stop_motion_mode", "mode")
        else:
            pie.operator_enum("object.mode_set", "mode")


def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_stop_motion.bl_idname,
        text="Add Stop Motion Object",
        icon='PLUGIN')


def extend_menus():
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def revert_menus():
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)

# Registration


def register():

    bpy.utils.register_class(VIEW3D_MT_PIE_StopMotion)
    bpy.utils.register_class(VIEW3D_MT_PIE_StopMotion_Mode)

    bpy.utils.register_class(StopMotionPanel)
    extend_menus()
    KeyMaps.map(bpy.context)


def unregister():
    KeyMaps.unmap()
    revert_menus()
    bpy.utils.unregister_class(StopMotionPanel)

if __name__ == "__main__":
    register()
