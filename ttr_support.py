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
#  Time remapping add-on support module
#  (c) 2020 Andrey Sokolov (so_records)

import bpy, inspect, time, datetime, pathlib

class StatusError(Exception): pass
class DriversError(Exception): pass
class TMBVersionError(Exception): pass
class NoFramesError(Exception): pass
class NoKeyframesError(Exception): pass
ttr_exceptions = (
    StatusError, DriversError, TMBVersionError, NoFramesError, NoKeyframesError) 
        
def ttr_frame_info_update(self, context):
    bpy.ops.ttr.update()

class TTR_Helpers():
     
    def frame_handler_add(self):
        if ttr_frame_info_update not in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.append(ttr_frame_info_update)
    
    def frame_handler_remove(self):
        while ttr_frame_info_update in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.remove(ttr_frame_info_update)
    
    def timer_add(self, tick=.01):
        self.timer = self.wm.event_timer_add(tick, window=self.win)
    
    def timer_remove(self):
        try: self.wm.event_timer_remove(self.timer)
        except: pass
    
    def frame_set(self, sc, frame):
        sc.frame_set(int(frame), subframe=frame-int(frame))
        
    def set_mb(self, sc_obj, shutter, samples):
        sc = sc_obj.scene
        if sc_obj.type == 'CYCLES':
            sc.render.motion_blur_shutter = shutter
        elif sc_obj.type == 'TMB':
            sc.true_mb.shutter = shutter
            sc.true_mb.samples = samples
        elif sc_obj.type == 'BLENDER_EEVEE':
            sc.eevee.motion_blur_shutter = shutter
            if bpy.app.version_string.startswith("2.8"):
                sc.eevee.motion_blur_samples = samples
            else:
                sc.eevee.motion_blur_steps = samples
        sc.update_tag()
        
    def ttr_set_attributes(self, attributes):
        '''Set attributes from ttr_store as Operator self attributes'''
        all_atrs = [at for at in dir(self.ttr_store) if not at.startswith('_')
                    and not inspect.ismethod(getattr(self.ttr_store, at))]
        for at in attributes:
            if at in all_atrs:
                setattr(self, at, getattr(self.ttr_store, at))
            else:            
                raise StatusError(f'{at} for {self.bl_idname} is not in storage')

class TTR_ShowSupport(TTR_Helpers):

    def preview_quit(self, context, type='BACK'):
        if type == 'BACK':
            frame = self.frame_current
            self.frame_set(self.main_sc, frame)
        elif type == 'FROM':
            frame = self.index+1+self.skip_start
            self.frame_set(self.main_sc, frame)
        if self.sc_obj.mb:
            self.set_mb(self.sc_obj, self.sc_obj.shutter, self.sc_obj.samples)
        msg = 'Escape Preview mode'
        bpy.ops.ttr.warning('INVOKE_DEFAULT', type='INFO', msg = msg)
        self.frame_handler_add()
        self.timer_remove()
        self.main_sc.use_nodes = self.use_nodes
        bpy.ops.ttr.setup(op='UPD')
            
    def step_left(self, fstep):
        self.index = self.index-fstep if self.index >= fstep > 0 else 0
        self.main_sc.ttr.number = self.index+1
        self.main_sc.ttr.actual = self.frames[self.index]
        self.frame_set(self.main_sc, self.frames[self.index])
        if self.sc_obj.mb:
            samples = self.sc_obj.samples_list[self.index] if self.sc_obj.samples_list else None
            shutter = self.sc_obj.shutter_list[self.index] if self.sc_obj.shutter_list else None
            self.set_mb(self.sc_obj, shutter, samples)
        bpy.ops.ttr.warning('INVOKE_DEFAULT', type='INFO', msg = self.msg)
        
    def step_right(self, fstep):
        self.index = (  self.index+fstep
                        if self.index+fstep < len(self.frames)
                        else len(self.frames)-1 )
        self.main_sc.ttr.number = self.index+1
        self.main_sc.ttr.actual = self.frames[self.index]
        self.frame_set(self.main_sc, self.frames[self.index])
        if self.sc_obj.mb:
            samples = self.sc_obj.samples_list[self.index] if self.sc_obj.samples_list else None
            shutter = self.sc_obj.shutter_list[self.index] if self.sc_obj.shutter_list else None
            self.set_mb(self.sc_obj, shutter, samples)
        bpy.ops.ttr.warning('INVOKE_DEFAULT', type='INFO', msg = self.msg)    
    
    def show_setup(self, context):
        self.frame_handler_remove()
        self.use_nodes = self.main_sc.use_nodes
        self.main_sc.use_nodes = False
        self.index = self.main_sc.ttr.number-1        
        #------------------- jump to the start if the coursor is below the start
        self.index = self.index if self.index >= 0 else 0
        self.main_sc.ttr.number = self.index+1
        self.main_sc.ttr.actual = self.frames[self.index]
        self.started = False
        self.frame_set(self.main_sc, self.frames[self.index])
        if self.sc_obj.mb:
            samples = self.sc_obj.samples_list[self.index] if self.sc_obj.samples_list else None
            shutter = self.sc_obj.shutter_list[self.index] if self.sc_obj.shutter_list else None
            self.set_mb(self.sc_obj, shutter, samples)
        self.wm = context.window_manager
        self.win = context.window
        self.timer_add()

class TTR_PlaySupport(TTR_Helpers):

    def play_setup(self, context):
        self.op = bpy.types.TTR_OT_play
        self.op.instances_running += 1
        if self.op.instances_running > 1:
            self.frame_handler_add()
            raise StatusError ()
        self.use_nodes = self.main_sc.use_nodes
        self.main_sc.use_nodes = False
        self.frame_handler_remove()
        self.frame_len = len(self.frames)
        self.counter = 0
        self.step = 1/int(self.main_sc.render.fps)
        self.wm = context.window_manager
        self.win = context.window
        self.timer_add(tick = self.step)

class TTR_CommonSupport(TTR_Helpers):
    
    def structure(self, context):
        self.indicies = list(range(len(self.frames)))
        self.use_nodes = self.main_sc.use_nodes
        self.path = self.main_sc.render.filepath
        self.wm = context.window_manager
        self.win = context.window
        self.timer = self.wm.event_timer_add(.1, window=self.win)
        self.frame_handler_remove()
            
    def cleanup(self, type="render"):
        self.wm.event_timer_remove(self.timer)
        self.frame_set(self.main_sc, self.frame_current)
        for sc_obj in self.scenes:
            self.frame_set(sc_obj.scene,sc_obj.start_frame)
            if sc_obj.mb:
                self.set_mb(sc_obj, sc_obj.shutter, sc_obj.samples)
            if type == "render":
                try: bpy.ops.ttr.fixnames(clear=True)
                except: print("TTR Render. Could not clear files")
                self.render_handler_remove()
        self.main_sc.render.filepath = self.path
        self.frame_handler_add()
        if type == "viewport":
            bpy.ops.ttr.update()
    
    def frame_prepare(self):        
        if self.animation:
            self.frame = self.frames.pop(0)
            self.ttr_store.index = self.indicies.pop(0)
        else:
            num = self.main_sc.ttr.actual_number
            self.frame = self.frames[num-1] if num else self.frames[0]
            self.ttr_store.index = num-1 if num else 0
        self.main_sc.render.filepath = self.path + f'{int(self.ttr_store.index+self.skip_start+1):04d}'
        if self.bl_idname == 'TTR_OT_render' and self.ttr_store.index:
            bpy.ops.ttr.fixnames()
        for sc_obj in self.scenes:
            self.frame_set(sc_obj.scene, self.frame)
            if sc_obj.shutter_list:
                if self.animation:
                    shutter = sc_obj.shutter_list.pop(0)
                    samples = sc_obj.samples_list.pop(0)
                else:
                    shutter = sc_obj.shutter_list[self.ttr_store.index]
                    samples = sc_obj.samples_list[self.ttr_store.index]
                self.set_mb(sc_obj, shutter, samples)
                    
    def setup_and_abort(self, context):
        if self.main_sc.render.image_settings.file_format in (
                                            'AVI_JPEG', 'AVI_RAW', 'FFMPEG'):
            msg = "Sorry!\nTrue Time Remapping currently doesn't support render\
 in\n\"AVI JPEG\", \"AVI Raw\" and \"FFmpeg video\" File Formats.\n\nPlease\
 change Output File Format in\nOutput Properties -> Output\n\nTip: If you need\
 to render animation, you may render image sequences."
            bpy.ops.ttr.warning('INVOKE_DEFAULT', type = 'ERROR', msg=msg)
            raise StatusError(msg)
        if ( self.bl_idname == 'TTR_OT_render' and
        not [obj for obj in self.main_sc.objects if obj.type == 'CAMERA'] ):
            msg = f'Error: No camera found in scene "{sc.name}"'
            bpy.ops.ttr.warning('INVOKE_DEFAULT', type = 'ERROR', msg=msg)
            raise StatusError(msg)

class TTR_FoSupport(TTR_Helpers):
        
    def fix_prefix(self, fo):
        for fs in fo.file_slots:
            if self.on:
                fs.path = (fs.path if self.fpth_prefix in fs.path
                                   else self.fpth_prefix+fs.path )
            else:
                fs.path = fs.path.replace(self.fpth_prefix, "")
    
    def get_fouts(self):
        if (self.main_sc.use_nodes and self.main_sc.node_tree
        and self.main_sc.node_tree.nodes):
            for nd in self.main_sc.node_tree.nodes:
                if nd.type == 'OUTPUT_FILE' and not nd.mute:
                    self.fix_prefix(nd)
                    bp = bpy.path.abspath(nd.base_path)
                    if self.on and bp not in self.fo_paths:
                        self.fo_paths.append(bp)
            if not self.on:
                self.fo_paths.clear()

class TTR_FoNamesSupport(TTR_CommonSupport):
    
    def fix_fp_name(self, name): # ----------- TTR fix index in file name  ---------------
        '''Change filepath according to True Time Remapping add-on settings'''
        name_list = name.split('.')
        name_list[-2] = name_list[-2][:-4]+f'{int(self.ttr_store.index+self.skip_start):04d}'
        new_name = ''
        for i in name_list:
            new_name+=i
            new_name+='.'
        if self.fpth_prefix in new_name:
            new_name = new_name.replace(self.fpth_prefix, "")
        print(f"TTR. {name} name changed to {new_name}")
        return new_name[:-1]

    def fix_files_names(self): # ------------------------ Move Image to Render Path ---------------
        '''Fix file outputs names'''
        for fp in self.fo_paths:
            spath = pathlib.Path(fp)
            if not spath.is_dir():
                continue
            for child in pathlib.Path(spath).glob('*'):
                ch_path = str(child)
                if child.is_file() and self.fpth_prefix in ch_path:
                    new_name = self.fix_fp_name(child.name)
                    new_path = ch_path.replace(child.name, new_name)
                    if pathlib.os.path.exists(new_path):
                        old = pathlib.Path(new_path)
                        if old.is_file():
                            old.unlink()                        
                    child.rename(new_path)
    
    def clear_if_fo_remains(self):
        for fp in self.fo_paths:
            spath = pathlib.Path(fp)
            if not spath.is_dir():
                continue
            for child in pathlib.Path(spath).glob('*'):
                ch_path = str(child)
                if child.is_file() and self.fpth_prefix in ch_path:
                    child.unlink()

class TTR_RenderSupport(TTR_CommonSupport):
    
    def __init__(self):
        self.t1 = time.perf_counter()
        
    def __del__(self):
        if hasattr(self, 'tmb') and self.tmb and self.tmb_launch:
            self.frame_handler_remove()
            bpy.ops.tmb_render.render('INVOKE_DEFAULT',
                    animation = True if self.animation else False,
                    write_still = True if self.animation else False,
                    use_viewport = True)
            return
        if hasattr(self, 't1'):
            self.t2 = time.perf_counter()
            total_time = str(datetime.timedelta(seconds=(self.t2-self.t1)))
            msg = f'Total Render Time: {total_time[:-3]}'
            bpy.ops.ttr.warning('INVOKE_DEFAULT', type = "INFO", msg = msg)
            bpy.ops.ttr.fo_prefixes(on=False)
            try: bpy.ops.ttr.fixnames()
            except AssertionError: print('TTR. No files to fix names')
            try: self.cleanup()
            except: print('TTR. Render cleanup failed')

    def render_handler_add(self):
        _ttr_store = self.ttr_store
        def pre(self, context):
            _ttr_store.started = True
            
        def complete(self, context):
            _ttr_store.started = False
            _ttr_store.ready = True
        
        def final(self, context):
            _ttr_store.finished = True
        
        self.pre = pre
        self.complete = complete
        self.final = final
        bpy.app.handlers.render_pre.append(self.pre)
        bpy.app.handlers.render_complete.append(self.complete)
        
    def render_handler_remove(self):
        while self.complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.complete)
        while self.final in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.final)
        while self.pre in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.remove(self.pre)
    
    def render_handler_final(self):
        while self.complete in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.complete)
        while self.final in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self.final)
        bpy.app.handlers.render_complete.append(self.final)
        
    def restore_from_tmb(self, context):
        '''Prepare project for instant native render'''
        
        sc = context.scene
        if not self.main_sc.node_tree or not self.main_sc.node_tree.nodes:
            return
        #------------------------------- Turn off all TMB Mix (Alpha Over) nodes
        for node in self.main_sc.node_tree.nodes:
            if node.name.startswith('TMB_Mix') and node.type == 'ALPHAOVER':
                node.inputs[0].default_value = 0
    
    def render(self):
        bpy.ops.render.render('INVOKE_DEFAULT', animation = False,
        write_still = True if self.animation else False, use_viewport = True)
    
    def render_setup(self, context):
        try: self.setup_and_abort(context)
        except ttr_exceptions: return {'FINISHED'}
        self.structure(context)
        self.render_handler_add()
        bpy.ops.ttr.fo_prefixes()
        self.ttr_store.ready = True
        self.ttr_store.started = False
        self.ttr_store.finished = False

class TTR_OpenglSupport(TTR_CommonSupport):
    
    def __init__(self):
        self.t1 = time.perf_counter()
    
    def __del__(self):        
        if hasattr(self, 'tmb') and self.tmb and self.tmb_enabled:
            self.frame_handler_remove()
            bpy.ops.tmb_render.opengl('INVOKE_DEFAULT', animation=self.animation)
            return
        if hasattr(self, 't1'):
            self.t2 = time.perf_counter()
            total_time = str(datetime.timedelta(seconds=(self.t2-self.t1)))
            msg = f'Total Render Time: {total_time[:-3]}'
            bpy.ops.ttr.warning('INVOKE_DEFAULT', type = "INFO", msg = msg)
        if hasattr(self, 'started') and self.started:
            if not self.showing:
                bpy.ops.render.view_show('INVOKE_DEFAULT')
            try: self.cleanup(type="viewport")
            except: print("OpenGL Render cleanup failed")
      
    def render_frame(self):
        self.frame_prepare()
        bpy.ops.render.opengl(animation=False,
            write_still=True if self.animation else False,
            view_context=True)
        if self.main_sc.ttr.preview and not self.showing and self.animation:
            bpy.ops.render.view_show('INVOKE_DEFAULT')
            self.showing = True
        self.ready = True
