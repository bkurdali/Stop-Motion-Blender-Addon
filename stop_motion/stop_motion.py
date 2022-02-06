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
    importlib.reload(json_nodes)
    importlib.reload(preferences)
else:
    from . import json_nodes
    from . import preferences

import bpy
import os


MODNAME = "StopMotion"
COLNAME = "StopMotion Sources"

# Data  Helpers


class Modifier():
    """ Convenience Stop Motion Modifier Access Class """

    def __init__(self, obj):
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
        return self.modifier.node_group.inputs[input].identifier

    @property
    def index(self):
       return self.modifier[self.__index__]

    @index.setter
    def index(self, value):
        self.modifier[self.__index__] = value

    @property
    def collection(self):
        return self.modifier[self.__collection__]

    @collection.setter
    def collection(self, value):
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


def int_to_str(index):
    """ Lets us play with formatting later """
    return f"{index:04}"

# Main Operators


class StopMotionOperator(bpy.types.Operator):
    """ Save Typing some Things """
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object and Modifier(context.object) 


class OBJECT_OT_add_stop_motion(bpy.types.Operator):
    """Create a new stop motion Object with an initial keyframe"""
    bl_idname = "object.add_stop_motion"
    bl_label = "Add Stop Motion Object"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        
        scene = context.scene
        stop_motion_object = context.object

        # Create Source Collection (initialize with selection)
        stop_motion_collection = bpy.data.collections.new(
            name=COLNAME)
        # Instead of linking fake user to prevent accidents
        stop_motion_collection.use_fake_user = True
        stop_motion_collection.hide_render = True
        stop_motion_collection.hide_viewport = True

        first_frame = stop_motion_object.copy()
        first_frame.name = int_to_str(0)
        old_collections = [
            c for c in bpy.data.collections if first_frame.name in c]
        for c in old_collections:
            c.objects.unlink(first_frame)
        stop_motion_collection.objects.link(first_frame)        
        
        # Create and Populate Modifiers
        for name, json_path, modname in (
                ("MeshKey", "modifier.json", MODNAME),
                ("Realize", "realizer.json", "Realizer")):
            node_group = json_nodes.read_node(
                name, os.path.join(os.path.dirname(__file__), json_path))
            modifier = stop_motion_object.modifiers.new(modname, 'NODES')
            modifier.node_group = node_group
        modifier.show_viewport = modifier.show_in_editmode = False # Don't realize by default

        modifier = Modifier(stop_motion_object) # for convenient access
        modifier.collection = stop_motion_collection
        modifier.index = 0
        modifier.keyframe_index(context)

        return {'FINISHED'}

# Animation Operators


def insert_keyframe(context, source_data, use_copy=False):
    """ Appends a keyshape at end; doesn't disrupt the alphabetical order """
    obj = context.object
    if not obj:
        return
    modifier = Modifier(obj)
    if not modifier:
        return
    mode = obj.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    collection = modifier.collection
    
    latest = max((ob.name for ob in collection.objects), default="0000")
    newest = int_to_str(int(latest) + 1)
    index = len(collection.objects)
    
    if not source_data:
        source_data = collection.objects[int_to_str(modifier.index)].data
        use_copy = True # Always copy the current shape if keyframing it
    
    shape_data = source_data.copy() if use_copy else source_data
    shape_ob = bpy.data.objects.new(name=newest, object_data=shape_data)
    
    collection.objects.link(shape_ob)
    modifier.index = index
    modifier.keyframe_index(context)

    obj.data = shape_ob.data
    bpy.ops.object.mode_set(mode=mode)


class OBJECT_OT_keyframe_stop_motion(StopMotionOperator):
    """Add a key drawing/ frame, optionally from selection"""
    bl_idname = "object.keyframe_stop_motion"
    bl_label = "New Keyframe"
    
    use_copy: bpy.props.BoolProperty(default=True)
    
    def execute(self, context):
        stop_motion_object = context.object
        possible_sources = (
            o for o in context.selected_objects
            if o is not stop_motion_object and o.type == 'MESH')
        for source in possible_sources:
            insert_keyframe(context, source.data, use_copy=self.use_copy)
            return {'FINISHED'} # We only care about 1 selected object
        insert_keyframe(context, None, use_copy=True)
        return {'FINISHED'}


class OBJECT_OT_Join_keyframe_stop_motion(StopMotionOperator):
    """Join Selected Meshes into a new keyframe"""
    bl_idname = "object.join_stop_motion"
    bl_label = "Join Keyframe"

    @classmethod
    def poll(cls, context):
        return (
            StopMotionOperator.poll(context) and context.mode == 'OBJECT'
            and len(context.selected_objects) > 1)

    def execute(self, context):
        stop_motion_object = context.object
        insert_keyframe(context, None, use_copy=True)
        mode = stop_motion_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}


class SCREEN_OT_next_or_add_key(bpy.types.Operator):
    """Goto next available keyframe, add one if unavailable"""
    bl_idname = "screen.next_or_keyframe_stop_motion"
    bl_label = "Next/Add Next Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    frame_offset: bpy.props.IntProperty(default=0, min=0, soft_min=1, max=100)
    use_copy: bpy.props.BoolProperty(default=True)

    first_run = True

    def fallback(self):
        result = bpy.ops.screen.keyframe_jump()
        if result == {'CANCELLED'}:
            self.report(
                {'WARNING'}, "No more keyframes to jump in this direction")
        return result

    def execute(self, context):

        modifier = Modifier(context.object)
        if not modifier or modifier.future_keys(context):
            return self.fallback()

        # Set the offset to addon preferences on first run
        if SCREEN_OT_next_or_add_key.first_run:
            SCREEN_OT_next_or_add_key.first_run = False
            preferences = context.preferences.addons[__package__].preferences
            self.frame_offset = preferences.frame_offset

        if self.frame_offset == 0:
            return self.fallback()

        context.scene.frame_set(context.scene.frame_current + self.frame_offset)
        return bpy.ops.object.keyframe_stop_motion(use_copy=self.use_copy)

# Import / Export


class OBJECT_OT_import_stop_motion_obj(StopMotionOperator):
    """Import obj as a key drawing"""
    bl_idname = "object.import_stop_motion_obj"
    bl_label = "Import OBJ"

    filepath: bpy.props.StringProperty(default="")

    def execute(self, context):
        if not self.filepath:
            self.report({'WARNING'}, "Save Blend File First")
            return {'CANCELLED'}
        stop_motion_object = context.object
        bpy.ops.import_scene.obj(
            filepath=self.filepath, use_split_objects=True,
            use_split_groups=False, use_groups_as_vgroups=True,
            use_image_search=True, split_mode='ON', global_clamp_size=0,
            use_edges=False, use_smooth_groups=False,
            axis_forward='Y', axis_up='Z')
        imported_objects = bpy.context.selected_objects
        bpy.ops.object.keyframe_stop_motion(use_copy=False)
        for ob in imported_objects:
            if ob is not stop_motion_object:
                bpy.data.objects.remove(ob, do_unlink=True)
        stop_motion_object.select_set(True)
        return {'FINISHED'}


class OBJECT_OT_export_stop_motion_obj(StopMotionOperator):
    """Export current frame as an obj"""
    bl_idname = "object.export_stop_motion_obj"
    bl_label = "Export OBJ"

    filepath:bpy.props.StringProperty(default="")

    def execute(self, context):
        if not self.filepath:
            self.report({'WARNING'}, "Save Blend File First")
            return {'CANCELLED'}
        stop_motion_object = context.object
        modifier = Modifier(stop_motion_object)
        mode = stop_motion_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        data = modifier.collection.objects[int_to_str(modifier.index)].data
        stop_motion_object.data = data
        # export obj with the right settings
        bpy.ops.export_scene.obj(
            filepath=self.filepath,
            check_existing=False, use_selection=True,
            use_animation=False, use_mesh_modifiers=False, use_edges=False,
            use_smooth_groups=False, use_smooth_groups_bitflags=False,
            use_normals=False, use_uvs=False, use_materials=False,
            use_triangles=False, use_nurbs=False, use_vertex_groups=False,
            use_blen_objects=True, group_by_object=False,
            group_by_material=False, keep_vertex_order=True,
            global_scale=1, path_mode='AUTO',
            axis_forward='Y', axis_up='Z'
            )
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}

# Mode wrappers


def update_data(scene):
    """ update object data as quickly as possible in non object modes """  

    ob = bpy.context.object 
    mode = ob.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data = bpy.data.objects[int_to_str(Modifier(ob).index)].data
    bpy.ops.object.mode_set(mode=mode)


class OBJECT_OT_stop_motion_mode(StopMotionOperator):
    """Switch Mode with corrected meshes """
    bl_idname = "object.stop_motion_mode"
    bl_label = "Stop Motion Mode"
    
    mode: bpy.props.EnumProperty(
        items = [
            ('OBJECT', 'Object Mode', 'OBJECT', 'OBJECT_DATAMODE', 0),
            ('EDIT', 'Edit Mode', 'EDIT', 'EDITMODE_HLT', 1),
            ('SCULPT', 'Sculpt Mode', 'SCULPT', 'SCULPTMODE_HLT', 2),
            ('VERTEX_PAINT', 'Vertex Paint Mode', 'VERTEX_PAINT', 'VPAINT_HLT', 3),
            ('WEIGHT_PAINT', 'Weight Paint Mode', 'WEIGHT_PAINT', 'MOD_VERTEX_WEIGHT', 4),
            ('TEXTURE_PAINT', 'Texture Paint Mode', 'TEXTURE_PAINT', 'TPAINT_HLT', 5)],
        default='OBJECT')

    toggle: bpy.props.BoolProperty(default=False)

    def execute(self, context):

        ob = context.object
        modifier = Modifier(ob)
        if modifier:
            collection = modifier.collection
            index = modifier.index


            # put the correct object_data in
            sources = sorted([o for o in collection.objects], key=lambda o:o.name)
            ob.data = sources[index].data

            if self.toggle and self.mode == ob.mode:
                print("here, ", self.mode, ", object", ob.mode)
                self.mode = 'OBJECT'

            if self.mode == 'OBJECT':
                for handler in bpy.app.handlers.frame_change_post:
                    if handler.__name__ == update_data.__name__:
                        bpy.app.handlers.frame_change_post.remove(handler)
            else:
                bpy.app.handlers.frame_change_post.append(update_data)
        
        return bpy.ops.object.mode_set(mode=self.mode, toggle=self.toggle)


def is_handler_running():
    return any([update_data.__name__ == handler.__name__ for handler in bpy.app.handlers.frame_change_post])


class OBJECT_OT_stop_motion_updater_toggle(bpy.types.Operator):
    """Start / Stop the Updater"""
    bl_idname = "object.stop_motion_updater_toggle"
    bl_label = "Toggle Updater"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        modifier = Modifier(obj)
        running = is_handler_running()
        if not modifier:
            return running
        object_mode = obj.mode == 'OBJECT'
        if object_mode:
            return running
        return not running

    def execute(self, context):
        handlers = bpy.app.handlers.frame_change_post
        for handler in handlers:
            if handler.__name__ == update_data.__name__:
                bpy.app.handlers.frame_change_post.remove(handler)
                break
        else:
            bpy.app.handlers.frame_change_post.append(update_data)
        return {'FINISHED'}


# UI


# Keymaps

class KeyMaps():


    settings = (
        ("Frames", 'EMPTY', SCREEN_OT_next_or_add_key.bl_idname, 'UP_ARROW', {}, {}),
        ("3D View", 'VIEW_3D', "wm.call_menu_pie", 'D',{}, {'name': 'VIEW3D_MT_PIE_StopMotion'}),
        ("Object Non-modal", 'EMPTY', "wm.call_menu_pie", 'TAB', {'ctrl': 1}, {'name': 'VIEW3D_MT_PIE_StopMotion_Mode'}),
        ("Object Non-modal", 'EMPTY', OBJECT_OT_stop_motion_mode.bl_idname, 'TAB', {'ctrl': 0}, {'mode': 1, 'toggle': True})
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
            elif operator == OBJECT_OT_stop_motion_mode.bl_idname:
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
    """ Draw the first Button, just for the panel"""
    ob = context.object
    mod = Modifier(ob)
    row = item_func(layout)
    if not mod:
        row.operator(
            OBJECT_OT_add_stop_motion.bl_idname,
            text="", icon='PLUS')
        return
    object_mode = ob.mode
    act_mode_item = bpy.types.Object.bl_rna.properties["mode"].enum_items[object_mode]
    act_mode_i18n_context = bpy.types.Object.bl_rna.properties["mode"].translation_context
    row.operator_menu_enum(
        OBJECT_OT_stop_motion_mode.bl_idname, "mode",
        text="",
        icon=act_mode_item.icon,
    )



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
        (OBJECT_OT_keyframe_stop_motion.bl_idname, "", 'DECORATE_KEYFRAME', {"use_copy": True}),
        (SCREEN_OT_next_or_add_key.bl_idname, "", 'NEXT_KEYFRAME', {}),
        (OBJECT_OT_Join_keyframe_stop_motion.bl_idname, "", 'MOD_BOOLEAN', {})
    ]
    obj_operators = [
        [OBJECT_OT_export_stop_motion_obj.bl_idname, "", 'CURRENT_FILE', {}],
        [OBJECT_OT_import_stop_motion_obj.bl_idname, "", 'FILE', {}]
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
        mod = Modifier(ob)
        
        flow = layout.split()

        col = flow.column()
        col.scale_y = 2

        draw_first(context, col, self.new_row)
        Draw(col, self.new_row, self.main_operators).buttons(context)
        path = context.blend_data.filepath.replace(".blend", f"_{ob.name}_frame.obj")
        for operator in self.obj_operators:
            operator[-1]["filepath"] = path
        drawer = Draw(col, self.new_row, self.obj_operators)
        drawer.buttons(context)
        running = is_handler_running()
        icon = 'PLAY' if not running else 'SNAP_FACE'
        drawer.button(operator=OBJECT_OT_stop_motion_updater_toggle.bl_idname, text="", icon=icon, props={})


# Menus


class VIEW3D_MT_PIE_StopMotion(bpy.types.Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Select Mode"


    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        # operator_enum will just spread all available options
        # for the type enum of the operator on the pie
        # pie.operator_enum("mesh.select_mode", "type")
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
            pie.operator_enum(OBJECT_OT_stop_motion_mode.bl_idname, "mode")
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
    
# Scratch Area

# Registration


def register():
    bpy.utils.register_class(OBJECT_OT_add_stop_motion) # Create and Initialize
    bpy.utils.register_class(OBJECT_OT_stop_motion_mode) # Mode Change Wrapper
    bpy.utils.register_class(OBJECT_OT_stop_motion_updater_toggle)
    bpy.utils.register_class(OBJECT_OT_import_stop_motion_obj)
    bpy.utils.register_class(OBJECT_OT_export_stop_motion_obj)
    bpy.utils.register_class(OBJECT_OT_keyframe_stop_motion) # Insert New Key
    bpy.utils.register_class(SCREEN_OT_next_or_add_key)
    bpy.utils.register_class(OBJECT_OT_Join_keyframe_stop_motion)

    bpy.utils.register_class(VIEW3D_MT_PIE_StopMotion)
    bpy.utils.register_class(VIEW3D_MT_PIE_StopMotion_Mode)

    bpy.utils.register_class(StopMotionPanel)
    extend_menus()
    KeyMaps.map(bpy.context)



def unregister():
    KeyMaps.unmap()
    revert_menus()
    bpy.utils.unregister_class(StopMotionPanel)

    bpy.utils.unregister_class(VIEW3D_MT_PIE_StopMotion)
    bpy.utils.unregister_class(VIEW3D_MT_PIE_StopMotion_Mode)
    bpy.utils.unregister_class(OBJECT_OT_stop_motion_updater_toggle)
    bpy.utils.unregister_class(OBJECT_OT_add_stop_motion)
    bpy.utils.unregister_class(OBJECT_OT_stop_motion_mode)
    bpy.utils.unregister_class(OBJECT_OT_import_stop_motion_obj)
    bpy.utils.unregister_class(OBJECT_OT_export_stop_motion_obj)
    bpy.utils.unregister_class(SCREEN_OT_next_or_add_key)
    bpy.utils.unregister_class(OBJECT_OT_keyframe_stop_motion)
    bpy.utils.unregister_class(OBJECT_OT_Join_keyframe_stop_motion)

if __name__ == "__main__":
    register()
