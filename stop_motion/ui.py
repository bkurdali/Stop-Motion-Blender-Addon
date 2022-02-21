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

# Panels


class AdapativePanel():

    small_icon = 80
    large_icon = 180
    # text gets displayed when width is larger than large icon

    def responsive(self, context):
        """Must be called first by draw function!!!"""
        self.width = context.region.width / context.preferences.view.ui_scale

    def scale(self):
        """set element scale based on region width"""
        if self.width < self.small_icon:
            return 1
        return 2

    def item_text(self, text):
        """Remove item label text when width is too small"""
        if self.width < self.large_icon:
            return ""
        return text

    def adaptive_row(self, layout):
        row = layout.row()
        row.scale_x = self.scale()
        return row

    def adaptive_col(self, layout):
        col = layout.column()
        col.scale_y = self.scale()
        return col

    def operator_button(self, layout, operator_id, text, icon, props):
        row = self.adaptive_row(layout)
        result = row.operator(
            operator_id, text=self.item_text(text), icon=icon)
        for prop, value in props.items():
            setattr(result, prop, value)
        return result

    def operator_menu_enum(self, layout, operator_id, text, icon, prop):
        row = self.adaptive_row(layout)
        result = row.operator_menu_enum(
            operator_id, prop,
            text=self.item_text(text),
            icon=icon)
        return result

    def pop_over(self, layout, panel, text, icon):
        row = self.adaptive_row(layout)
        row.popover(panel, text=self.item_text(text), icon=icon)


class StopMotionControls():
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


class StopMotionPanel(bpy.types.Panel, AdapativePanel, StopMotionControls):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = ""
    bl_idname = "OBJECT_PT_Stopmotion"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "StopMo"

    def draw(self, context):
        self.responsive(context)

        layout = self.layout

        ob = context.object
        mod = Modifier(ob)

        layout.use_property_split = True

        flow = layout.split()
        col = self.adaptive_col(flow)

        if not mod:
            self.operator_button(
                col, "object.add_stop_motion", "Initialize", 'PLUS', {})
            return

        icon = bpy.types.Object.bl_rna.properties["mode"].enum_items[ob.mode].icon
        menu = self.operator_menu_enum(
            col, "object.stop_motion_mode", "Set Mode", icon, "mode")
        menu.toggle = False
        col.separator(factor=0.8)

        for operator_list in (self.main_operators, self.obj_operators):
            for operator_id, text, icon, props in operator_list:
                self.operator_button(col, operator_id, text, icon, props)
            col.separator(factor=0.4)

        running = update_handler.is_running()
        icon = 'PLAY' if not running else 'SNAP_FACE'
        self.operator_button(
            col,
            "object.stop_motion_updater_toggle", "Toggle Updater", icon, {})
        col.separator(factor=0.4)

        self.pop_over(
            col,
            "OBJECT_PT_stopmotion_onion_skin", "Onion Skins", 'GP_MULTIFRAME_EDITING')


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
        layout.separator(factor=.5)
        row = layout.row()
        row.operator("object.sync_onion_skins", text="Refresh", icon='FILE_REFRESH')
        layout.separator(factor=1)


# Menus


class VIEW3D_MT_PIE_StopMotion(bpy.types.Menu, StopMotionControls):
    bl_label = "Select Mode"

    def new_row(self, layout, dummy=2):
        return layout

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        for operator_id, text, icon, props in self.main_operators:
            button = pie.operator(operator_id, text=text, icon=icon)
            for prop, value in props.items():
                setattr(button, prop, value)


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
            print("typical ")
            menu = pie.operator_enum("object.mode_set", "mode")
            menu.toggle = False


def add_object_button(self, context):
    self.layout.operator(
        "object.add_stop_motion",
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
