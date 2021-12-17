bl_info = {
    "name": "Schmod Blender Bindings",
    "description": "Schmod Hotkey system for making Blender usage less ass",
    "author": "Nicholas Reynolds",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "category": "Schmod",
}

# Test Commit Change

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
import mathutils
import rna_keymap_ui
import os
import math
from pathlib import Path

# Operators
class SchmodBindingSwapper(bpy.types.Panel):
    """Hotkey Switcher"""
    bl_label = "Hotkey Switcher"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        keymaps_path = Path(os.getenv('BLENDER_KEYMAPS_PATH'))
        blender_keymap = keymaps_path / 'Blender_Keymap.py'
        schmod_keymap = keymaps_path / 'Schmod_Keymap.py'
        
        # Get Base Layout
        lyo_main = self.layout

        lyo_box = lyo_main.box()
        lyo_keymaps = lyo_box.grid_flow()
        lyo_keymaps.operator('preferences.keyconfig_activate', text='', icon='BLENDER').filepath = str(blender_keymap)
        lyo_keymaps.operator('preferences.keyconfig_activate', text='', icon='EVENT_I').filepath = str(schmod_keymap)

class ContextualViewAxisSwap(bpy.types.Operator):
    bl_idname = 'wm.contextual_view_axis_swap'
    bl_label = 'Contextual View Axis Swap'

    swap_type: bpy.props.StringProperty(name='Swap Type')

    def __init__(self):
        super(ContextualViewAxisSwap, self).__init__()

    def execute(self, context):
        if self.swap_type is not None:
            is_view_persp = self.is_perspective()
            if is_view_persp:
                self.set_view_axis(self.swap_type)
            else:
                bpy.ops.view3d.view_persportho()
                cur_view_axis = self.get_ortho_view()
                if cur_view_axis != '':
                    if self.swap_type == cur_view_axis:
                        self.set_view_axis(self.get_opposing_view(cur_view_axis))
                    else:
                        self.set_view_axis(self.swap_type)
        
        return {'FINISHED'}

    def is_perspective(self):
        out = False
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                out = area.spaces.active.region_3d.is_perspective
        
        return out

    def get_ortho_view(self):
        out = ''
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                r3d = area.spaces.active.region_3d # fine for right-upper quadview view
                view_matrix = r3d.view_matrix

                out = self.get_view_orientation_from_matrix(view_matrix)
        
        return out

    def get_view_orientation_from_matrix(self, view_matrix):
        r = lambda x: round(x, 2)
        view_rot = view_matrix.to_euler()
        freeze_rot = view_rot.freeze()
        vec = (r(freeze_rot.x), r(freeze_rot.y), r(freeze_rot.z))

        orientation_dict = {(0.0, 0.0, 0.0) : 'TOP',
                            (r(math.pi), 0.0, 0.0) : 'BOTTOM',
                            (r(-math.pi/2), 0.0, 0.0) : 'FRONT',
                            (r(math.pi/2), 0.0, r(-math.pi)) : 'BACK',
                            (r(-math.pi/2), r(math.pi/2), 0.0) : 'LEFT',
                            (r(-math.pi/2), r(-math.pi/2), 0.0) : 'RIGHT'}
        out = None
        try:
            out = orientation_dict[vec]
        except:
            out = 'TOP'

        return out

    def get_opposing_view(self, view_axis):
        view_pair = {
            'TOP' : 'BOTTOM',
            'BOTTOM' : 'TOP',
            'FRONT' : 'BACK',
            'BACK' : 'FRONT',
            'LEFT' : 'RIGHT',
            'RIGHT' : 'LEFT'
            }

        return view_pair[view_axis]
    
    def set_view_axis(self, view_axis):
        bpy.ops.view3d.view_axis(type=view_axis)
        print (view_axis)

# Hotkeys
addon_keymaps = []

# https://github.com/pitiwazou/Scripts-Blender/blob/Older-Scripts/addon_keymap_template
def get_hotkey_entry_item(km, kmi_name, kmi_value):
    '''
    returns hotkey of specific type, with specific properties.name (keymap is not a dict, so referencing by keys is not enough
    if there are multiple hotkeys!)
    '''
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            if km.keymap_items[i].properties.name == kmi_value:
                return km_item
    return None

def get_addon_preferences():
    ''' quick wrapper for referencing addon preferences '''
    addon_preferences = bpy.context.user_preferences.addons[__name__].preferences
    return addon_preferences

def add_hotkeys():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # Swap Perspective/Ortho
        kmPerspOrtho = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmiPerspOrtho = kmPerspOrtho.keymap_items.new('view3d.view_persportho', 'NUMPAD_1', 'PRESS', key_modifier='SPACE')
        addon_keymaps.append((kmPerspOrtho, kmiPerspOrtho))

        # Contextual Top/Bottom
        kmTopBottom = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmiTopBottom = kmTopBottom.keymap_items.new('wm.contextual_view_axis_swap', 'NUMPAD_2', 'PRESS', key_modifier='SPACE')
        kmiTopBottom.properties.swap_type = 'TOP'
        addon_keymaps.append((kmTopBottom, kmiTopBottom))

        # Contextual Front/Back
        kmFrontBack = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmiFrontBack = kmFrontBack.keymap_items.new('wm.contextual_view_axis_swap', 'NUMPAD_3', 'PRESS', key_modifier='SPACE')
        kmiFrontBack.properties.swap_type = 'FRONT'
        addon_keymaps.append((kmFrontBack, kmiFrontBack))

        # Contextual Left/Right
        kmLeftRight = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmiLeftRight = kmLeftRight.keymap_items.new('wm.contextual_view_axis_swap', 'NUMPAD_4', 'PRESS', key_modifier='SPACE')
        kmiLeftRight.properties.swap_type = 'LEFT'
        addon_keymaps.append((kmLeftRight, kmiLeftRight))

        # Focus
        kmFocus = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmiFocus = kmFocus.keymap_items.new('view3d.view_selected', 'F', 'PRESS')
        addon_keymaps.append((kmFocus, kmiFocus))
        
        # Rotate
        kmRotateView = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmiRotateView = kmRotateView.keymap_items.new('view3d.rotate', 'LEFTMOUSE', 'PRESS', key_modifier='SPACE')
        addon_keymaps.append((kmRotateView, kmiRotateView))

        # Pan
        kmPanView = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmiPanView = kmPanView.keymap_items.new('view3d.move', 'MIDDLEMOUSE', 'PRESS', key_modifier='SPACE')
        addon_keymaps.append((kmPanView, kmiPanView))

        # Zoom
        kmZoomView = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmiZoomView = kmZoomView.keymap_items.new('view3d.zoom', 'RIGHTMOUSE', 'PRESS', key_modifier='SPACE')
        addon_keymaps.append((kmZoomView, kmiZoomView))

def remove_hotkeys():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    
    addon_keymaps.clear()

# Prefs
class SchmodBlenderBindingsPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    prefs_tabs: EnumProperty(items=(('general', "General", "General"), ('keymaps', "Keymaps", "Keymaps")), default='general')

    """filepath: StringProperty(
        name="Example File Path",
        subtype='FILE_PATH',
    )
    number: IntProperty(
        name="Example Number",
        default=4,
    )
    boolean: BoolProperty(
        name="Example Boolean",
        default=False,
    )"""

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        row = layout.row(align=True)
        row.prop(self, 'prefs_tabs', expand=True)

        if self.prefs_tabs == 'general':
            return

        if self.prefs_tabs == 'keymaps':
            box = layout.box()
            col = box.column()

            wm = context.window_manager
            kc = wm.keyconfigs.addon

            for km, kmi in addon_keymaps:
                col.context_pointer_set("keymap", km)
                rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

# Registration
operator_classes = [SchmodBindingSwapper, ContextualViewAxisSwap, SchmodBlenderBindingsPrefs]

def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)

    add_hotkeys()

def unregister():
    for cls in operator_classes:
        bpy.utils.unregister_class(cls)

    remove_hotkeys()

# Debug
if __name__ == "__main__":
    register()