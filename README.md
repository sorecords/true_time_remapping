# TRUE TIME REMAPPING
# add-on for Blender 2.8+
Provides full control over the overall playback/render speed

# FEATURES
- Works in Eevee, Cycles and Workbench render engines
- Supports Multi-scenes setups and File Outputs nodes in the Compositor
- 2 different keyframe-able modes: change the whole Speed or set exact Frames
- Keyframe-able Motion Blur Stretch slider
- Compatible with the True Motion Blur add-on v.1.1.0+

# ABOUT SOURCE CODE
- The source code is provided under the GPL license. Supporting non-code files which are required for add-on to work in Blender are included only in paid versions, the links are below. You are free to edit the source code and remove this restrictions by yourself, but I don't provide help for this process, and can't support the end result

# INSTALL
ZIP file with add-on ready-to-install can be purchased here:
- Gumroad: (currently disabled due to sanctions)
- Blendermarket: (currently disabled due to sanctions)

- Donwnload ZIP file
- Don't unpack it!
- Open Blender. From top menu go to > Edit > Preferences > Add-ons > Install
- Find downloaded ZIP file and click "Install Add-on" button
- After add-on is installed check enabling checkbox near its name

# MAIN LOCATION
- Render Properties > True Time Remapping

# OTHER LOCATIONS
- Top Menu > Render > Render Time Remapped Frame
- Top Menu > Render > Render Time Remapped Animation
- 3D Viewport > View > Show Time Remapped Frame
- 3D Viewport > View > Play Time Remapped Animation
- 3D Viewport > View > Viewport Render Time Remapped Frame
- 3D Viewport > View > Viewport Render Time Remapped Animation


# INTERFACE
- Type: choose the time-remapping mode from "Speed", "Frames".
    "Speed" uses Speed slider.
    "Frames" uses Frame slider
- Speed: determines the speed at each frame on the timeline
- Frame: determines what frames will be played/rendered at the certain Timeline's frames (needs to be keyframed)
- Motion Blur Stretch: determines how much Time Remapping affects motion blur (stretches shutter and adjust samples when the speed is faster than original and does opposite when the speed is slower)
- Update button and info boxes:
    "Update" button you may need while working with keyframing to recalculate info
    "Total" shows how many frames will be played/rendered totally after time remapping
    "Actual frame" shows what actual frame will be shown/rendered at the current frame
    "Number" shows actual frame's number from the start of the time-remapped frame range
- Skip from Start/Skip from End: allows to crop the time-remapped frame range for playback/render
- Show Time Remapped Frame (Ctrl+Alt+S): enter the Preview mode which shows the actual frame that will be rendered at the current cursor position on the Timeline. In this mode you can scroll between time-remapped frames using mouse wheel, mouse buttons, keyboard up/down and left/up arrows, AD, <>, [], -+ buttons. Holding Ctrl speeds up dcrolling 10 times. And holding Ctrl+Shift speeds up scrolling even more - up to 50 times. To escape Preview mode press: Esc, Tab, Enter or Space - you will be returned to the frame you have entered from. Holding Shift while pressing any of those buttons will bring you to the frame where the current frame is supposed to be rendered. Holding Shift+Alt while pressing any of those buttons will escape Preview mode leaving you at the current time-remapped frame.
- Play Time Remapped Animation (Shift+Alt+Space): playback time-remapped animation in the 3D Viewport
- Render Time Remapped Frame (Shift+Alt+F12): render a single time-remapped frame
- Render Time Remapped Animation (Ctrl+Shift+Alt+F12): render time-remapped animation
- Viewport Render Time Remapped Frame (Shift+Alt+V): render a single OpenGL Viewport preview frame
- Viewport Render Time Remapped Animation (Ctrl+Shift+Alt+V): render OpenGL Viewport preview animation
- Show in Viewport: determines whether Viewport preview will be shown whileOpenGL Viewport render or not.
