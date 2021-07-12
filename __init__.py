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
#  Time remapping add-on for Blender 2.82+
#  (c) 2020 Andrey Sokolov (so_records)

bl_info = {
    "name": "True Time Remapping",
    "author": "Andrey Sokolov",
    "version": (1, 0, 1),
    "blender": (2, 83, 3),
    "location": "Render Settings > True Time Remapping",
    "description": "Time remapping",
    "warning": "",
    "wiki_url": "https://github.com/sorecords/true_time_remapping/blob/master/README.md",
    "tracker_url": "https://github.com/sorecords/true_time_remapping/issues",
    "category": "Render"
}

def register():
    from .ttr_ui import register as ui_register
    ui_register()
    from .ttr_ops import register as op_register
    op_register()
    
def unregister():
    from .ttr_ui import unregister as ui_unregister
    ui_unregister()
    from .ttr_ops import unregister as op_unregister
    op_unregister()