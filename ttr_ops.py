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
#  Time remapping add-on Blender Operators
#  (c) 2020 Andrey Sokolov (so_records)

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty
from .ttr_support import *
from .ttr_setup import TTR_Setup, ttr_store

class TTR_Warning(Operator):
    '''Warning!'''
    bl_idname = "ttr.warning"
    bl_label = "Warning!"
    type: StringProperty()
    msg : StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        return {'FINISHED'}
    
    def modal(self, context, event):
        if event:
            self.report({self.type}, self.msg)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class TTR_SetupLaunch(TTR_Helpers, Operator):
    bl_idname = "ttr.setup"
    bl_label = "TTR Setup Launch"
    op : StringProperty(default='UPD')
    
    def execute(self, context):
        global ttr_store
        ttr_store = None
        try: ttr_store = TTR_Setup(context, operator=self.op)
        except ttr_exceptions as err:
            if self.op == 'UPD':
                print("TTR. ERROR WAS HANDLED")
                pass
            else:
                print("TTR. ERROR WAS RAISED")
                return {'CANCELLED'}
        return {'FINISHED'}

class TTR_FO(TTR_FoSupport, Operator):
    '''Add/Remove prefix for File Outputs filepath names'''
    bl_idname = "ttr.fo_prefixes"
    bl_label = "TTR Setup Launch"
    on : BoolProperty(default=True)
    attributes = [
        "main_sc",
        "fo_paths",
        "fpth_prefix"
    ]
    ttr_store = None
    
    def execute(self, context):
        global ttr_store
        if not ttr_store:
            bpy.ops.ttr.setup()
        assert ttr_store
        self.ttr_store = ttr_store
        self.ttr_set_attributes(self.attributes)
        self.get_fouts()
        return {'FINISHED'}
    
class TTR_FixFilesNames(TTR_FoNamesSupport, Operator):
    '''Fix File Outputs' result files names'''
    bl_idname = "ttr.fixnames"
    bl_label = "TTR Fix Names"
    attributes = [
        "skip_start",
        "index",
        "fo_paths",
        "fpth_prefix"
    ]
    ttr_store = None
    clear : BoolProperty(default=False)
    
    def execute(self, context):
        global ttr_store
        assert ttr_store
        self.ttr_store = ttr_store
        self.ttr_set_attributes(self.attributes)
        if self.clear:
            self.clear_if_fo_remains()
        else:
            self.fix_files_names()
        return {'FINISHED'}
                
class TTR_UpdateFramesInfo(TTR_Helpers, Operator):
    '''Update frames info'''
    bl_idname = "ttr.update"
    bl_label = "Update Time Remapped Frames Info"
    
    def execute(self, context):
        bpy.ops.ttr.setup(op='UPD')
        self.frame_handler_remove()
        if context.scene.ttr.activate:
            self.frame_handler_add()
        return {'FINISHED'}

class TTR_RemoveUpdater(TTR_Helpers, Operator):
    '''Remove Update function from Frame Change handler'''
    bl_idname = "ttr.update_remove"
    bl_label = "Remove Update function from Frame Change handler"
    
    def execute(self, context):
        self.frame_handler_remove()
        return {'FINISHED'}
    
class TTR_Store(TTR_Helpers, Operator):
    '''Cross-add-ons storage'''
    bl_idname = 'ttr.store'
    bl_label = 'TTR Storage'
    ttr_store = None
    
    def execute(self, context):
        global ttr_store
        if not ttr_store:
            bpy.ops.ttr.update()
        bpy.types.TTR_OT_store.ttr_store = ttr_store
        return {'FINISHED'}

class TTR_ShowCurrent(TTR_ShowSupport, Operator):
    '''Show frame that will be rendered at current coursor position'''
    bl_idname = "ttr.show"
    bl_label = "Show Time Remapped Frame"
    attributes = [
        "frame_current",
        "frames",
        "index",
        "main_sc",
        "sc_obj",
        "scenes",
        "skip_start",
        "started",
        "timer",
        "use_nodes",
        "win",
        "wm",
    ]
    ev_quit = {'ESC', 'SPACE', 'RET', 'Q', 'TAB'}
    ev_prev = {'LEFT_ARROW', 'DOWN_ARROW', 'LEFT_BRACKET', 'LEFTMOUSE','A', 'S',
        'MINUS','WHEELDOWNMOUSE', '[', 'COMMA', 'MINUS', 'NUMPAD_MINUS'}
    ev_next = {'RIGHT_ARROW', 'UP_ARROW', 'RIGHT_BRACKET', 'RIGHTMOUSE','W','D', 
        'PLUS','WHEELUPMOUSE', ']', 'PERIOD', 'EQUAL', 'NUMPAD_PLUS'}
    ev_const = {'TIMER', 'MOUSEMOVE'}
    msg = 'Preview mode: ESC/TAB to escape. MOUSE buttons/wheel to scroll\
 between frames'
    ttr_store = None
    
    def execute(self, context):
        global ttr_store
        if bpy.ops.ttr.setup(op="SHOW") == {'CANCELLED'}:
            return {'FINISHED'}
        self.ttr_store = ttr_store
        self.ttr_set_attributes(self.attributes)
        self.show_setup(context)
        self.wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        fstep = 1
        if event.ctrl:
            fstep = 10
            if event.shift:
                fstep = 50 
                                   
        if event.type in self.ev_quit and event.value == 'PRESS':
            type = "BACK"
            if event.shift:
                if event.ctrl: type = 'STAY'
                else: type = 'FROM'
            self.preview_quit(context,type=type)
            return {'FINISHED'}
        elif event.type == 'S' and event.ctrl:
            if not self.started:
                self.started = True
            else:
                self.preview_quit(context)
                bpy.ops.wm.save_mainfile()
                return {'FINISHED'}
        elif event.type in self.ev_prev and event.value == 'PRESS':
            self.step_left(fstep)
        elif event.type in self.ev_next and event.value == 'PRESS':
            self.step_right(fstep)
        elif event.type not in self.ev_const and event.value == 'PRESS':
            bpy.ops.ttr.warning('INVOKE_DEFAULT', type='INFO', msg = self.msg)
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        return self.execute(context)

#--------------------------- Play Remapped Animation ---------------------------### PLAY ANIMATION ###

class TTR_Play(TTR_PlaySupport, Operator):
    '''Play Time Remapped Animation'''
    bl_idname = "ttr.play"
    bl_label = "Play Time Remapped Animation"
    attributes = [
        "op",
        "main_sc",
        "frames",
        "frame_current",
        "frame_len",
        "counter",
        "use_nodes",
        "frame_len",
        "counter",
        "step",
        "timer",
        "win",
        "wm",
    ]
    instances_running = 0
    ttr_store = None
    
    def execute(self, context):
        global ttr_store
        if bpy.ops.ttr.setup(op="PLAY") == {'CANCELLED'}:
            return {'FINISHED'}
        self.ttr_store = ttr_store
        self.ttr_set_attributes(self.attributes)
        self.play_setup(context)
        self.wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if ((event.type in ('ESC', 'SPACE', 'TAB') and event.value == 'PRESS')
                                        or self.op.instances_running > 1):
            self.timer_remove()
            if event.shift: # ---------------------------- stop at current frame
                context.scene.frame_set(self.main_sc.frame_current, subframe=0.0)
                bpy.ops.ttr.update()
            else: # ---------------------------- jump back to the starting frame
                self.frame_set(self.main_sc, self.frame_current)
            self.op.instances_running = 0
            self.frame_handler_add()
            self.main_sc.use_nodes = self.use_nodes
            bpy.ops.ttr.setup(op='UPD')
            return {'FINISHED'}
        elif event.type == 'TIMER':
            if self.counter == self.frame_len:
                self.counter = 0
            self.frame = self.frames[self.counter]
            self.frame_set(context.scene, self.frame)
            self.counter += 1
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        return self.execute(context)

#----------------------------------- Render ------------------------------------### RENDER ###

ttr_common_attributes = [
    'scenes',
    'main_sc',
    'sc_obj',
    'tmb',
    'tmb_enabled',
    'tmb_launch',
    'scenes',
    'frames',
    'indicies',
    'index',
    'main_sc',
    'use_nodes',
    'path',
    'wm',
    'win',
    'frame_current',
    'skip_start',
    'timer',
    'ready',
    'started',
    'pre',
    'complete',
    'final',
    'fpth_prefix',
    'fo_paths'
]

class TTR_Render(TTR_RenderSupport, Operator):
    '''Render Time Remapped Animation'''
    bl_idname = "ttr.render"
    bl_label = "Render Time Remapped Animation"
    animation : BoolProperty()
    attributes = ttr_common_attributes
    ttr_store = None
    
    def execute(self, context):
        global ttr_store
        if bpy.ops.ttr.setup(op="RENDER") == {'CANCELLED'}:
            return {'FINISHED'}
        self.ttr_store = ttr_store
        self.ttr_set_attributes(self.attributes)
        if self.tmb:
            if self.tmb_enabled:
                self.tmb_launch = True     
                return {'FINISHED'}
            else:
                self.restore_from_tmb(context)        
        if self.render_setup(context) == {'FINISHED'}:
            return {'CANCELLED'}
        self.wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        global ttr_store
        if event.type == "ESC":
            return {'FINISHED'}
        elif event.type == 'TIMER':
            if len(self.frames) == 0:
                if not ttr_store.started:
                    self.render_handler_final()
                    self.render()
                elif ttr_store.finished:
                    return {'FINISHED'}
            elif ttr_store.finished:
                return {'FINISHED'}
            elif ttr_store.ready:
                if not self.animation:
                    if self.final not in bpy.app.handlers.render_complete:
                        ttr_store.ready = False
                        self.frame_prepare()
                        self.render_handler_final()
                        self.render()
                    elif not ttr_store.started:
                        self.render()
                    return{'PASS_THROUGH'}
                else:
                    ttr_store.ready = False
                    self.frame_prepare()
                    self.render()
            elif not ttr_store.started:
                self.render()
        return{'PASS_THROUGH'}
    
    def invoke(self, context, modal):
        return self.execute(context)
    
#------------------------------- Viewport Render -------------------------------### VIEWPORT RENDER ###

class TTR_ViewportRender(TTR_OpenglSupport, Operator):
    '''Viewport Render Time Remapped Animation'''
    bl_idname = "ttr.opengl"
    bl_label = "Viewport Render Time Remapped Animation"
    animation : BoolProperty()
    attributes = ttr_common_attributes
    ttr_store = None
    
    def execute(self,context):
        global ttr_store
        if bpy.ops.ttr.setup(op="OPENGL") == {'CANCELLED'}:
            return {'FINISHED'}
        self.ttr_store = ttr_store
        self.ttr_set_attributes(self.attributes)
        if self.sc_obj.tmb:
            return {'FINISHED'}
        self.started = True
        try: self.setup_and_abort(context)
        except ttr_exceptions: return {'FINISHED'}
        self.structure(context)
        self.tmb=False
        self.showing = False
        self.ready = True
        self.wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        if event.type == "ESC":
            return {'CANCELLED'}
        elif event.type == 'TIMER':
            if len(self.frames) == 0:
                return {'FINISHED'}
            elif self.ready:
                self.ready = False
                self.render_frame()
                if not self.animation:
                    return {'FINISHED'}
        return{'PASS_THROUGH'}
    
    def invoke(self, context, modal):
        return self.execute(context)

#---------------------------------- Register -----------------------------------

classes = [
    TTR_Warning,
    TTR_SetupLaunch,
    TTR_FO,
    TTR_FixFilesNames,
    TTR_Play,
    TTR_ShowCurrent,
    TTR_Render,
    TTR_ViewportRender,
    TTR_UpdateFramesInfo,
    TTR_RemoveUpdater,
    TTR_Store,
]    

def register():
    for cl in classes:
        bpy.utils.register_class(cl)
    
def unregister():
    for cl in reversed(classes):
        bpy.utils.unregister_class(cl)
        
#--------------------------- For test purposes only ----------------------------   
if __name__ == '__main__':
    register()