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
#  TTR add-on project setup
#  (c) 2020 Andrey Sokolov (so_records)

#------------------------------- Import Modules --------------------------------

import bpy, addon_utils, inspect, numpy as np
from .ttr_support import *
global ttr_store
ttr_store = None

#--------------------- Supporting Functions and Operators ----------------------### SETUP ###

class TTR_Scene():
    '''Scene info'''
    
    def __init__(self, scene):
        self.scene = scene                              # scene
        self.engine = scene.render.engine               # scene render engine
        self.start_frame = scene.frame_current_final    # scene current frame        
        self.type = None        # enum in {'TMB', 'CYCLES', 'BLENDER_EEVEE'}
        self.mb = None          # Motion Blur (MB) enabled in scene
        self.shutter = None     # MB Shutter
        self.samples = None     # MB Samples
        self.shutter_list = []  # list of shutter values for each frame
        self.samples_list = []  # list of samples values for each frame
        self.tmb = None         # True Motion Blur (TMB) add-on enabled in scene
        self.tmb_shutter = None # TMB Shutter FCurve
        self.tmb_samples = None # TMB Samples FCurve
    
class TTR_Setup(TTR_Helpers):
    '''
    Get list of actual subframes to render after time remapping
    Set list length to `ttr.update` value to show in `ttr.frames`
    '''
    
    def __init__(self, context, operator="RENDER", animation=False):
        self._context = context
        self._operator = operator
        self._animation = animation
        self.wm = None               # context Window Manager
        self.win = None              # context Window
        self.main_sc = None          # active scene
        self.sc_obj = None           # active scene storage object
        self.path = None             # render filepath
        self.ttr_type = None         # enum in {'SPEED', 'FRAMES'}
        self.frame_start = 0         # active scene frame_start
        self.frame_end = 0           # active scene frame_end
        self.frame_current = 0       # active scene frame_current
        self.use_nodes = None        # active scene Compositor use nodes
        self.skip_start = None       # active scene TTR skip start parameter
        self.skip_end = None         # active scene TTR skip end parameter
        self.data_path = ""          # enum in {'ttr.speed', 'ttr.frames'}
        self.fcurve = None           # data_path FCurve
        self.fdrive = None           # data_path Drivers
        self.compensate = None       # MB Stretch Fcurve
        self.frames = []             # remapped frames list
        self.indicies = []           # remapped frames indicies list
        self.scenes = []             # scenes classes
        self.composites = []         # Compositor Composite nodes list
        self.fo_paths = []           # File Outputs paths
        self.fpth_prefix = "ttr.tmp."# File paths prefix
        # handlers
        self.pre = None              # bpy.app.handlers.render_pre function
        self.complete = None         # bpy.app.handlers.render_complete function
        self.final = None            # bpy.app.handlers.render_complete function
        self.timer = None            # Operator Timer        
        # modal
        self.frame = None            # current frame
        self.index = None            # current frames list index
        self.ready = None            # Operator is ready to render next frame
        self.started = False         # original Render Operator have launched        
        self.op = None               # self operator
        self.frame_len = 0           # total frames number for playback
        self.counter = 0             # current frame while playback
        self.step = 0                # time offset between frames while playback
        self.showing = False         # Operator is showing Viewport while render
        self.finished = False        # True if the last frame render is finished
        self.tmb_launch = None       # reroute render to TMB
        self.t1 = None               # start time
        self.t2 = None               # finish time
        # True Motion Blur add-on settings
        self.tmb = None                 # True Motion Blur (TMB) add-on installed
        self.tmb_enabled = None         # TMB enabled for some scenes
        self.tmb_version = None         # TMB version
        self.tmb_launch = None          # Confirmation of launching TMB render
        
        self.setup(context, operator, animation) # execute initialization
    
    #------------------------------ check_enabled ------------------------------
    
    def _check_enabled(self, context):
        if not context.scene.ttr.activate:
            msg='True Time Remapping is disabled for this scene'
            if not self._operator == 'UPD':                
                type = "WARNING"
                bpy.ops.ttr.warning('INVOKE_DEFAULT',type=type,msg=msg)
            raise StatusError(msg)
            
    #------------------------------ project_info -------------------------------
    
    def _check_drivers(self):
        '''Cancel if drivers are used for TTR parameters'''
        ad = self.main_sc.animation_data
        if (ad and ad.drivers and [fc for fc in ad.drives if
        fc.data_path in ('ttr.speed', 'ttr.frame', 'ttr.mb')]):
            msg = "Sorry. True Time Remapping add-on doesn't work with drivers"
            type = "WARNING"
            bpy.ops.ttr.warning('INVOKE_DEFAULT',type=type,msg=msg)
            raise DriversError(msg)

    def _check_tmb_version(self):
        '''Cancel if the True Motion Blur version is outdated'''
        versions = [adn.bl_info.get('version', (-1,-1,-1)) 
                    for adn in addon_utils.modules()
                    if adn.bl_info['name'] == 'True Motion Blur']
        version = versions[0] if versions else None
        if version and version in ((1,0,0),(1,0,1),(1,0,2)):
            self.tmb = False
            if self.main_sc.true_mb.activate:
                msg = "Update True Motion Blur add-on to v.1.1.0 or higher\
 to use together with True Time Remapping"
                bpy.ops.ttr.warning('INVOKE_DEFAULT',type='WARNING',msg=msg)
                raise TMBVersionError(msg)
        return version
    
    def _get_fcurve(self, scene, data_path):
        fcurves = [fc for fc in scene.animation_data.action.fcurves
                                            if fc.data_path == data_path]
        return fcurves[0] if fcurves else None
    
    def _project_info(self, context):
        self.main_sc = context.scene
        self._check_drivers()
        self.tmb = True if hasattr(bpy.types, "TMB_RENDER_OT_render") else False
        self.tmb_version = self._check_tmb_version() if self.tmb else None
        self.ttr_type = self.main_sc.ttr.type
        self.data_path = "ttr.speed" if self.ttr_type=="SPEED" else "ttr.frame"
        self.frame_start = self.main_sc.frame_start
        self.frame_end = self.main_sc.frame_end
        self.frame_current = self.main_sc.frame_current_final
        self.skip_start = self.main_sc.ttr.skip_start
        self.skip_end = ( None if not self.main_sc.ttr.skip_end else
                          self.main_sc.ttr.skip_end) 
        self.start_frame = self.frame_current
        self.frames = []
        # ------ Get Time Remapping and MB Compensate FCurves to Evaluate ------
        ad = self.main_sc.animation_data
        if ad and ad.action and ad.action.fcurves:
            self.fcurve = self._get_fcurve(self.main_sc, self.data_path)            
            self.compensate = self._get_fcurve(self.main_sc, "ttr.mb")
        else:
            self.fcurve = None
            self.compensate = None
    
    #------------------------------- get_scenes --------------------------------
        
    def _get_scenes(self, context):
        self.scenes = [TTR_Scene(self.main_sc)]
        if (self.main_sc.use_nodes and self.main_sc.node_tree
        and self.main_sc.node_tree.nodes):
            for node in self.main_sc.node_tree.nodes:
                if node.type == 'R_LAYERS' and node.scene not in self.scenes:
                    self.scenes.append(TTR_Scene(node.scene))
    
    #----------------------------- get_scenes_info -----------------------------
    
    def _get_tmb_fcurves(self, sc_obj):
        '''Get True Motion Blur add-on FCurves'''
        sc = sc_obj.scene
        if sc.animation_data and sc.animation_data.action:
            sc_obj.tmb_samples = self._get_fcurve(sc, "true_mb.samples")
            sc_obj.tmb_shutter = self._get_fcurve(sc, "true_mb.shutter")

    def _get_mb(self, sc_obj):
        sc = sc_obj.scene
        if sc_obj.mb:
            sc_obj.shutter_list = []
            sc_obj.samples_list = []
            if sc_obj.type == 'CYCLES':
                sc_obj.shutter = sc.render.motion_blur_shutter
                sc_obj.samples = 0
            elif sc_obj.type == 'BLENDER_EEVEE':
                sc_obj.shutter = sc.eevee.motion_blur_shutter
                sc_obj.samples = (
                    sc.eevee.motion_blur_samples
                    if bpy.app.version_string.startswith("2.8") else
                    sc.eevee.motion_blur_steps
                    )
            elif sc_obj.type == 'TMB':
                sc_obj.shutter = sc.true_mb.shutter
                sc_obj.samples = sc.true_mb.samples
        else:
            sc_obj.shutter = None
            sc_obj.samples = None

    def _get_scenes_info(self, context):
        tmb_check = False
        for sc_obj in self.scenes:
            sc = sc_obj.scene
            if sc == self.main_sc:
                self.sc_obj = sc_obj
            sc_obj.tmb = ( True if 
                ((# ----------------------- Case 1:
                self._operator == 'RENDER' and self.tmb and
                sc_obj.engine in ('BLENDER_EEVEE', 'BLENDER_WORKBENCH') and
                sc.true_mb.activate
                ) or (# ------------------- Case 2:
                self._operator in ('OPENGL','PLAY','SHOW') and self.tmb and
                sc == self.main_sc and                
                sc.true_mb.activate
                ) or (# ------------------- Case 3:
                self._operator == 'UPD' and self.tmb and
                sc.true_mb.activate
                ))
                else False )
            if sc_obj.tmb:
                tmb_check = True
                self._get_tmb_fcurves(sc_obj)
            sc_obj.type = "TMB" if sc_obj.tmb else sc_obj.engine
            sc_obj.mb = (True if any((
                                sc_obj.type == 'TMB', #--------------------1
                                (sc_obj.type == 'CYCLES' and #-------------2
                                sc.render.use_motion_blur),
                                (sc_obj.type == 'BLENDER_EEVEE' and #------3
                                sc.eevee.use_motion_blur)
                                ))
                        else False)
            self._get_mb(sc_obj)
        self.tmb_enabled = True if tmb_check else False
    
    #------------------------------- get_frames --------------------------------
            
    def _get_mb_info(self, sc_obj, step, frame):
        '''Get Scene motion Blur Info'''
        mb = (self.compensate.evaluate(frame)
                if self.compensate else self.main_sc.ttr.mb)
        fac = 1-((1-abs(step))*mb)
        if sc_obj.tmb: # ----------------------- for True Motion Blur add-on
            shutter = (fac * sc_obj.shutter if not sc_obj.tmb_shutter
                        else fac * sc_obj.tmb_shutter.evaluate(frame))                        
            samples = ( fac * sc_obj.samples if not sc_obj.tmb_samples
                        else fac * sc_obj.tmb_samples.evaluate(frame))
        else: # --------------------------------------- for original Motion Blur
            shutter = fac * sc_obj.shutter
            samples = fac * sc_obj.samples
        sc_obj.shutter_list.append(shutter)
        sc_obj.samples_list.append(max(1,round(samples)))

    def _speed(self, context):
        '''
        Calculate Frames and motion blur (if needed) values lists,
        if Time Remapping type is set to Speed.
        '''
        frames = self.frames
        start = self.frame_start
        current_frame = float(start)
        actual_frame = float(start)
        speed_frame = start
        frame_range = self.frame_end - self.frame_start
        remapped_range = 0
        gotcurrent = False
        
        # --------------------------- Get Frames List --------------------------
        while remapped_range <= (frame_range+0.01):
            frames.append(current_frame)
            # ------------------- Get next actual frame step -------------------
            step = ((1/100)*self.fcurve.evaluate(speed_frame)
                    if self.fcurve else
                    (1/100)*self.main_sc.ttr.speed)            
            # -------- Prevent Freezing when the Speed is close to Zero --------
            zero_step = step
            if abs(step) < .01:
                next = ( self.fcurve.evaluate(actual_frame+0.011)
                        if self.fcurve else self.main_sc.ttr.speed )
                if next < 0:
                    step = -0.01
                elif not step and not next:
                    step = 0.01
                    zero_step = 0
                else:
                    step = 0.01
            # ------- Get new Shutter and Samples values for Motion Blur -------            
            for sc_obj in self.scenes:
                if sc_obj.mb:
                    self._get_mb_info(sc_obj, zero_step, speed_frame)
            # ------------ Increment While loop values to continue -------------                    
            if abs(step) <= .01:
                current_frame += zero_step
            else:
                current_frame += step
            
            actual_frame += abs(step)
            remapped_range += abs(step)
            fstep = 1
            speed_frame += fstep
            #----------------------- Update Actual Frame -----------------------
            #--------------------- if in full frame range ----------------------
            if (speed_frame <= self.frame_current < speed_frame+fstep):
                gotcurrent = True
                #----------------------- if in cropped frame range -------------
                if len(frames) >= self.skip_start:                   
                    self.main_sc.ttr.number = len(frames)-self.skip_start+1
                    self.main_sc.ttr.actual = frames[-1] + zero_step
                #----------------------- if before frame range -----------------
                else: 
                    self.main_sc.ttr.number = 0
                    self.main_sc.ttr.actual = frames[-1]
            #------------ if not caught during the full frame range ------------
            elif remapped_range >= (frame_range+0.01) and not gotcurrent:
                #----------------------- if earlier than cropped frame range ---
                if len(frames) <= self.skip_start:
                    pass
                elif self.frame_current <= frames[self.skip_start]:
                    self.main_sc.ttr.number = 0
                    self.main_sc.ttr.actual = frames[self.skip_start]
                #----------------------- if later than cropped frame range -----
                else:
                    self.main_sc.ttr.number = len(frames)-self.skip_start+1
                    self.main_sc.ttr.actual = frames[-1]

        # ----------------- Check if there are frames to render ----------------
        total=len(frames)-self.skip_start+(self.skip_end if self.skip_end else 0)
        if total <= 0:
            msg = "No frames to render"
            bpy.ops.ttr.warning('INVOKE_DEFAULT', type="WARNING", msg=msg)
            self.main_sc.ttr.update = 0
            self.main_sc.update_tag()
            raise NoFramesError(msg)
        # ------------------------ Correct frames list -------------------------
        self.main_sc.ttr.update = total
        self.frames[:] = frames[self.skip_start:self.skip_end]
        for sc_obj in self.scenes:
            if sc_obj.mb:
                sc_obj.shutter_list = (
                            sc_obj.shutter_list[self.skip_start:self.skip_end])
                sc_obj.samples_list = (
                            sc_obj.samples_list[self.skip_start:self.skip_end])
        frames = self.frames
        if gotcurrent and self.main_sc.ttr.actual<frames[0]:
            self.main_sc.ttr.actual = frames[0]
        if self.main_sc.ttr.number >= total:
            self.main_sc.ttr.number=total
            self.main_sc.ttr.actual=frames[-1]
        return True
            
    def _frame(self, context):
        '''
        Calculate Frames and motion blur (if needed) values lists,
        if Time Remapping Type is set to Frames.
        '''
        # --------------- Check that Frame is animated or Cancel ---------------        
        if not self.fcurve:
            msg = '"Frame" parameter needs to be keyframed in "Frames" mode'
            bpy.ops.ttr.warning( 'INVOKE_DEFAULT',type='WARNING',msg=msg)
            self.frames = np.arange(self.frame_start,self.frame_end+1,1) 
            raise NoKeyframesError(msg)    
        # ------------------ Check there are frames to render ------------------
        sub_step = 1
        start = self.frame_start+self.skip_start
        end = self.frame_end+sub_step+(0 if not self.skip_end else self.skip_end)
        if start >= end:
            msg = "No frames to render"
            bpy.ops.ttr.warning('INVOKE_DEFAULT', type="WARNING", msg=msg)
            self.main_sc.ttr.update = 0
            self.main_sc.update_tag()
            raise NoFramesError(msg)
        # ------------------------- Get Frames List ----------------------------
        frames = np.arange(start, end, sub_step)
        self.frames = np.vectorize(self.fcurve.evaluate)(frames)
        self.frames = list(self.frames)
        fr = self.frames
        fr_len = len(fr)
        self.main_sc.ttr.update = fr_len
        for sc_obj in self.scenes:
            if not sc_obj.mb:
                continue
            # ------- Store new Shutter and Samples/Steps for Motion Blur ------           
            for n in range(fr_len):
                if n == 0:
                    step = abs(fr[n+1]-fr[n])
                elif n == (fr_len-1):
                    step = abs(fr[n]-fr[n-1])
                else:                
                    if fr[n-1]<fr[n]<fr[n+1] or fr[n-1]>fr[n]>fr[n+1]:
                        step = abs(fr[n+1]-fr[n-1])/2
                    else:
                        step = 0
                self._get_mb_info(sc_obj, step, fr[n])
        # ----------------------- Update Actual Frame --------------------------        
        if self.frame_current < start:
            self.main_sc.ttr.number = self.frame_current-start+self.frame_start
            self.main_sc.ttr.actual = -1
        elif self.frame_current > end:
            self.main_sc.ttr.number = len(fr)
            self.main_sc.ttr.actual = fr[-1]
        else:
            for n in range(len(fr)):
                if frames[n] == int(self.frame_current):
                    self.main_sc.ttr.actual = fr[n]
                    self.main_sc.ttr.number = n+1
        
    def _get_frames(self, context):
        if self.ttr_type == "SPEED":
            self._speed(context)
        else:
            self._frame(context)
        self.main_sc.update_tag()
        return True
    
    def setup(self, context, operator, animation):
        self._check_enabled(context)
        self._project_info(context)
        self._get_scenes(context)
        self._get_scenes_info(context)
        self._get_frames(context)

#--------------------- Supporting Functions and Operators ----------------------### SETUP ###
        
def ttr_setup_prop(self, context):
    bpy.ops.ttr.setup(op='UPD')