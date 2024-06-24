# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "BlenderUmap NG",
    "author" : "Amrsatrio, MountainFlash (MinshuG), Car_Killer",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View3D > Properties > Umap",
    "warning" : "",
    "doc_url": "https://github.com/Amrsatrio/BlenderUmap2/blob/master/README.md",
    "category" : "Add Mesh"
}


# auto_load.init()
from . import main
from . import settings
from . import uefn

modules = [main, settings, uefn]

def register():
    import importlib
    for m in modules:
        importlib.reload(m)
        m.register()

def unregister():
    for m in modules:
        m.unregister()

if __name__ == "__main__":
    register()
