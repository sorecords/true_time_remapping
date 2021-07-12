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

#  TRUE TIME REMAPPING
#  Time remapping add-on UI
#  (c) 2020 Andrey Sokolov (so_records)

import bpy, bpy.utils.previews, rna_keymap_ui, os
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
    )
from .ttr_setup import *
from .ttr_support import ttr_frame_info_update, ttr_exceptions

#---------------------------- Handler Functions --------------------------------
    
def ttr_frames_number(self):
    return bpy.context.scene.ttr.update 

def ttr_actual_frame(self):
    return bpy.context.scene.ttr.actual

def ttr_actual_number(self):
    return bpy.context.scene.ttr.number

#----------------------------------- UI ----------------------------------------

class TTR_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        global ttr_keymaps
        layout = self.layout
        layout.label(text="Time Remapping Shortcuts: ")
        col = layout.column()
        kc = bpy.context.window_manager.keyconfigs.addon
        km = (kc.keymaps.new("Screen") if "Screen" not in kc.keymaps
                                            else kc.keymaps['Screen'])
        for km, kmi in ttr_keymaps:
            km = km.active()
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
            
def ttr_keyconfig():
    global ttr_keymaps
    ttr_keymaps = []
    kc = bpy.context.window_manager.keyconfigs.addon
    km = (kc.keymaps.new("Screen") if "Screen" not in kc.keymaps
                                            else kc.keymaps['Screen'])
    for kmi in km.keymap_items:
        if kmi.idname.startswith("ttr."):
            kmi.active = True
            ttr_keymaps.append((km, kmi))
    if ttr_keymaps:
        return
    new = km.keymap_items.new
    kmi = new("ttr.update", 'U', 'PRESS', ctrl=True)
    kmi.active = True
    ttr_keymaps.append((km, kmi))
    kmi = new("ttr.show", 'S', 'PRESS', ctrl=True, alt=True)
    kmi.active = True
    ttr_keymaps.append((km, kmi))
    kmi = new("ttr.play", 'SPACE', 'PRESS', shift=True, alt=True)
    kmi.active = True
    ttr_keymaps.append((km, kmi))    
    kmi = new("ttr.render", 'F12', 'PRESS',ctrl=True, shift=True, alt=True)
    kmi.properties.animation = True
    kmi.active = True
    ttr_keymaps.append((km, kmi))    
    kmi = new("ttr.render", 'F12', 'PRESS', shift=True, alt=True)
    kmi.properties.animation = False
    kmi.active = True
    ttr_keymaps.append((km, kmi))
    kmi = new("ttr.opengl", 'V', 'PRESS', shift=True, alt=True)
    kmi.properties.animation = False
    kmi.active = True
    ttr_keymaps.append((km, kmi))
    kmi = new("ttr.opengl", 'V', 'PRESS', shift=True, ctrl=True, alt=True)
    kmi.properties.animation = True
    kmi.active = True
    ttr_keymaps.append((km, kmi))

def ttr_topmenu_draw(self, context):
    '''Drawing function to extend Top Menu'''
    if not context.scene.ttr.activate:
        return
    layout = self.layout
    layout.separator()
    still = layout.operator("ttr.render", text="Render Time Remapped Frame",
                                                        icon='RENDER_STILL')
    still.animation = False
    anim = layout.operator("ttr.render", text="Render Time Remapped Animation",
                                                        icon='RENDER_ANIMATION')
    anim.animation = True

def ttr_viewmenu_draw(self, context):
    '''Drawing function to extend View Menu'''
    if not context.scene.ttr.activate:
        return
    global ttr_icons
    layout = self.layout
    layout.separator()
    layout.operator("ttr.show", icon_value=ttr_icons['ttr_show_icon'].icon_id)
    layout.operator('ttr.play', icon = "PLAY")
    layout.separator()
    vstill = layout.operator("ttr.opengl", text = "Viewport Render\
 Time Remapped Frame", icon = "RENDER_STILL")
    vstill.animation = False
    vanim = layout.operator("ttr.opengl", icon = "RENDER_ANIMATION")
    vanim.animation = True

def ttr_menu_extend():
    if hasattr(bpy.types, "TTR_OT_render"):
        bpy.types.TOPBAR_MT_render.append(ttr_topmenu_draw)
        bpy.types.VIEW3D_MT_view.append(ttr_viewmenu_draw)
        
def ttr_menu_collapse():
    if hasattr(bpy.types, "TTR_OT_render"):
        bpy.types.TOPBAR_MT_render.remove(ttr_topmenu_draw)
        bpy.types.VIEW3D_MT_view.remove(ttr_viewmenu_draw)

def ttr_activate(self, context):
    '''Activate function to be used in Blender Properties'''
    global ttr_enabled
    if not ttr_enabled:
        ttr_menu_extend()
        ttr_keyconfig()
        ttr_enabled = True
    bpy.ops.ttr.update()
    print("TTR. Activated.")
    while ttr_activate in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(ttr_activate)
    print("")

#--------------------------------- Blender UI ----------------------------------
    
class TTR_Props(bpy.types.PropertyGroup):
    '''Properties Group for UI Panel'''
    
    activate : BoolProperty(
        name="",
        description="Enable",
        default=False,
        update=ttr_activate
    )
    type : EnumProperty(
        name = "Type",
        description = "Time remapping based on:",
        items = [
            ("FRAMES", "Frames",
                "The shutter opens on the current frame."),
            ("SPEED", "Speed",
                "The shutter is open during the current frame."),           
        ],
        default="SPEED",
        options={"HIDDEN"},
        update=ttr_setup_prop
    )
    frame : FloatProperty(
        name="Frame",
        description="Current Frame",
        default=1,
        soft_min = 0,
        soft_max = 1000,
        subtype = "FACTOR",
        update=ttr_setup_prop
    )
    speed : FloatProperty(
        name="Speed",
        description="Playback/Render Speed",
        default=100.0,
        soft_min = 0,
        soft_max=300.0,
        subtype = "PERCENTAGE",
        step = 1,
        update=ttr_setup_prop
    )
    frames : IntProperty(
        name="Total",
        description="Total number of frames to be rendered",
        options={"HIDDEN"},
        subtype='FACTOR',
        get=ttr_frames_number
    )
    skip_start : IntProperty(
        name="Skip from Start",
        description="Skip frames from the start of the Time Remapped frame range.\n\
For Playback, Render and Viewport Render",
        min=0,
        default=0,
        options={"HIDDEN"},
        update=ttr_setup_prop
    )
    skip_end : IntProperty(
        name="Skip from End",
        description="Skip frames from the end of the Time Remapped frame range.\n\
For Playback, Render and Viewport Render",
        max=0,
        default=0,
        options={"HIDDEN"},
        update=ttr_setup_prop
    )
    actual : FloatProperty(
        name="Frame",
        description="Hidden property to take the actual frame from",
        options={"HIDDEN"},
        default=1,
    )
    actual_frame : FloatProperty(
        name="",
        description="Actual frame(+subframe) which will be rendered at the\
 current cursor position",
        options={"HIDDEN"},
        subtype='NONE',
        get=ttr_actual_frame
    )
    number : IntProperty(
        name="",
        description="Hidden property to get updated Total Frames from",
        options={"HIDDEN"},
        default=1,
    )
    actual_number : IntProperty(
        name="Number",
        description="Number of actual frame in the frames list",
        options={"HIDDEN"},
        subtype='FACTOR',
        get=ttr_actual_number
    )
    update : IntProperty(
        name="Total frames",
        description="Hidden property to get updated Total Frames from",
        options={"HIDDEN"},
        default=250,
        min=0
    )
    mb : FloatProperty(
        name="Motion Blur Stretch",
        description="Stretch Motion Blur Shutter (and Samples/Steps for EEVEE)\
 to match Time Remapping.\nAffects only Render",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )
    preview : BoolProperty(
        name="Show in Viewport",
        description="While Viewport Render open Viewport to see results",
        default=False,
        options={"HIDDEN"}
    )

class TTR_PT_panel(bpy.types.Panel):
    '''Create UI Panel in the render properties window'''
    bl_label = "True Time Remapping"
    bl_idname = "RENDER_PT_ttr"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = "render"
    bl_category = 'True Time Remapping'
    
    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.ttr
        
        col = layout.column()
        col.prop(props, "activate")
        
    def draw(self, context):
        global ttr_icons        
        layout = self.layout
        layout.use_property_split = True
        scene = context.scene
        props = scene.ttr
        layout.active = props.activate
        
        col = layout.column()
        col.prop(props, "type")
        col = layout.column()
        col.enabled = True if context.scene.ttr.type == 'SPEED' else False
        col.prop(props, "speed")
        col = layout.column()
        col.enabled = True if context.scene.ttr.type == 'FRAMES' else False
        col.prop(props, "frame")
        col = layout.column()
        col.prop(props, "mb")
        col = layout.column()
        col.use_property_split = False
        tab = col.split(factor=.1)
        tab.operator("ttr.update", text = "", icon = "FILE_REFRESH")
        tab.prop(props, "frames", text="Total")
        tab.prop(props, "actual_frame")
        tab.prop(props, "actual_number", text="Number")
        col = layout.column()
        col.use_property_split = False
        tab = col.split()
        tab.prop(props, "skip_start")
        tab.prop(props, "skip_end")
        col.use_property_split = True
        col.separator()
        col.operator("ttr.show", text = "Show Time Remapped Frame",
                        icon_value = ttr_icons['ttr_show_icon'].icon_id)
        col.operator("ttr.play", text="Play Time Remapped Animation", icon = "PLAY")
        col.separator()
        _still = col.operator("ttr.render", text="Render Time Remapped Frame",
                                                    icon = "RENDER_STILL")
        _still.animation = False
        
        _anim = col.operator("ttr.render", text="Render Time Remapped Animation",
                                                    icon = "RENDER_ANIMATION")
        _anim.animation = True
        
        col.separator()
        _vstill = col.operator("ttr.opengl",
            text="Viewport Render Time Remapped Frame", icon = "RENDER_STILL")
        _vstill.animation = False
        _vanim = col.operator("ttr.opengl",
            text="Viewport Render Time Remapped Animation", icon = "RENDER_ANIMATION")
        _vanim.animation = True
        col.prop(props, "preview")
        
#---------------------------------- Register -----------------------------------
def ttr_uninstall():
    global keymap_items
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if 'Screen' in kc.keymaps:
        km = kc.keymaps['Screen']
        for kmi in km.keymap_items:
            if kmi.idname.startswith("ttr."):
                 km.keymap_items.remove(kmi)
    bpy.types.TOPBAR_MT_render.remove(ttr_menu_extend)
    
#---------------------------------- Register -----------------------------------

classes = [
    TTR_Props,
    TTR_Preferences,
    TTR_PT_panel,
]    

def foo(self, context):
        '''
        For some reason Blender ignores some functions in load_post handler.
        This is an empty function to kick in ttr_activate function.
        Hope it works in the most cases.
        '''
        pass

def register():
    directory = os.path.join(os.path.dirname(os.path.realpath(__file__)),"icons")
    icon_path = os.path.join(directory, 'ttr_icon.png')    
    if not os.path.exists(icon_path) and os.path.isfile(icon_path):
        bl_info["warning"] = "No valid icon. True Time Remapping add-on won't work"
        return
    
    global ttr_icons, ttr_enabled
    ttr_enabled = False
    try: bpy.utils.previews.remove(ttr_icons)
    except: pass
    ttr_icons = bpy.utils.previews.new()
    ttr_icons.load("ttr_show_icon", icon_path, 'IMAGE')
    
    for cl in classes:
        bpy.utils.register_class(cl)
    bpy.types.Scene.ttr = PointerProperty(type=TTR_Props)
    
    bpy.app.handlers.persistent(foo)
    bpy.app.handlers.load_post.append(foo)
    bpy.app.handlers.persistent(ttr_activate)
    bpy.app.handlers.load_post.append(ttr_activate)
    bpy.app.handlers.persistent(ttr_frame_info_update)
    if ttr_frame_info_update not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(ttr_frame_info_update)
    
def unregister():
    directory = os.path.join(os.path.dirname(os.path.realpath(__file__)),"icons")
    icon_path = os.path.join(directory, 'ttr_icon.png')
    if not (os.path.exists(icon_path) and os.path.isfile(icon_path)):
        return
    global ttr_icons, ttr_enabled
    try:
        ttr_menu_collapse()
    except:
        pass
    bpy.utils.previews.remove(ttr_icons)
    ttr_uninstall()
    for cl in reversed(classes):
        bpy.utils.unregister_class(cl)
    while ttr_activate in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(ttr_activate)
    while ttr_frame_info_update in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(ttr_frame_info_update)
    while foo in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(foo)
    ttr_enabled = False


#--------------------------- For test purposes only ----------------------------   
if __name__ == '__main__':
    register()