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
    width = context.region.width
    row = item_func(layout, 2 if width > 100 else 1)
    if not mod:
        row.operator(
            "object.add_stop_motion",
            text="Initialize" if width > 200 else "", icon='PLUS')
        return
    icon = bpy.types.Object.bl_rna.properties["mode"].enum_items[ob.mode].icon
    row.operator_menu_enum(
        "object.stop_motion_mode", "mode",
        text="Set Mode" if width > 200 else "",
        icon=icon)


class Draw():
    sizes = (100, 200)

    def __init__(self, layout, item_func, operators):
        self.layout = layout
        self.item_func = item_func
        self.operators = operators

    def button(self, operator, text, icon, props):
        """ Draw a single Button """
        item = self.item_func(self.layout, 2 if self.width > self.sizes[0] else 1).operator(
            operator,
            text=text if self.width > self.sizes[1] else "", icon=icon
            )
        for prop, value in props.items():
            setattr(item, prop, value)

    def buttons(self, context):
        """ All the Operator Buttons """
        # Operator idname, text, icon, props dict
        self.width = context.region.width
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
            "object.keyframe_stop_motion", "Insert Keyframe", 'DECORATE_KEYFRAME',
            {"use_copy": True}),
        ("screen.next_or_keyframe_stop_motion", "Next/New Keyframe", 'NEXT_KEYFRAME', {}),
        ("object.join_stop_motion", "Join Meshes", 'MOD_BOOLEAN', {}),
    ]
    obj_operators = [
        ("object.export_stop_motion_obj", "Export to OBJ", 'CURRENT_FILE', {}),
        ("object.import_stop_motion_obj", "Import from OBJ", 'FILE', {}),
    ]

    def new_row(self, layout, scale=2):
        row = layout.row()
        row.ui_units_x = 200
        row.scale_x = scale
        return row

    def draw(self, context):
        flow = layout = self.layout
        layout.use_property_split = True

        ob = context.object

        flow = layout.split()

        col = flow.column()
        width = context.region.width
        col.scale_y = 2 if width > 100 else 1

        draw_first(context, col, self.new_row)
        if Modifier(ob):
            col.separator(factor=0.8)
            Draw(col, self.new_row, self.main_operators).buttons(context)
            col.separator(factor=0.4)
            drawer = Draw(col, self.new_row, self.obj_operators)
            drawer.buttons(context)
            col.separator(factor=0.4)
            running = update_handler.is_running()
            icon = 'PLAY' if not running else 'SNAP_FACE'
            drawer.button(
                operator="object.stop_motion_updater_toggle",
                text="Toggle Updater" if width > 100 else "", icon=icon, props={})
            col.separator(factor=0.4)

            row = self.new_row(col, 2 if width > 100 else 1)
            row.popover("OBJECT_PT_stopmotion_onion_skin", text="Onion Skins" if width > 200 else "", icon='GP_MULTIFRAME_EDITING')


class OnionSkinPanel(bpy.types.Panel):
    bl_label = "Onion Skin"
    bl_idname = "OBJECT_PT_stopmotion_onion_skin"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        pass


class OnionSkinSettingsPanel(bpy.types.Panel):
    bl_label = "Enable"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'OBJECT_PT_stopmotion_onion_skin'

    def draw_header(self, context):
        settings = context.object.onion_skin_settings
        self.layout.prop(settings, "enable", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.object.onion_skin_settings

        layout.active = settings.enable
        col = layout.column(align=True)
        # layout.prop(settings, "enable")
        col.prop(settings, "frame_offset")
        col.prop(settings, "opacity")
        layout.separator(factor=1.0)
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(settings, "before", text="")
        row.label(text="", icon='GP_MULTIFRAME_EDITING')
        row.prop(settings, "after", text="")
        row = col.row(align=True)
        row.prop(settings, "before_color", text="")
        row.label(text="", icon='COLORSET_03_VEC')
        row.prop(settings, "after_color", text="")


# Menus


class VIEW3D_MT_PIE_StopMotion(bpy.types.Menu):
    bl_label = "Select Mode"

    def new_row(self, layout, dummy=2):
        return layout

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        Draw(pie, self.new_row, StopMotionPanel.main_operators).buttons(context)


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

    bpy.utils.register_class(OnionSkinPanel)
    bpy.utils.register_class(OnionSkinSettingsPanel)

    bpy.utils.register_class(StopMotionPanel)
    extend_menus()
    KeyMaps.map(bpy.context)


def unregister():
    KeyMaps.unmap()
    revert_menus()
    bpy.utils.unregister_class(StopMotionPanel)
    bpy.utils.unregister_class(OnionSkinSettingsPanel)
    bpy.utils.unregister_class(OnionSkinPanel)

    bpy.utils.unregister_class(VIEW3D_MT_PIE_StopMotion)
    bpy.utils.unregister_class(VIEW3D_MT_PIE_StopMotion_Mode)

if __name__ == "__main__":
    register()
