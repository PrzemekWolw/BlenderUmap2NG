import os
import subprocess
import typing
from io import StringIO
import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty
from bpy.types import Context

from .config import Config
from .utils import get_exporter_executable


classes = []

def register_class(cls):
    classes.append(cls)
    return cls


@register_class
class UEFN_PT_Panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Umap"
    bl_context = "objectmode"

    bl_label = "UEFN"


    def draw(self, context):
        layout = self.layout

        scene = context.scene

        col = layout.column()
        col.operator("umap.listuefnmaps", text="Fetch Cached UEFN Maps", icon="WORLD_DATA")
        col.label(text="Available Maps:")
        row = col.row()
        row.template_list("UEFN_MAP_UL_List", "UEFN_MAP_List", scene, "uefn_maps", scene, "uefn_list_index", rows=5)
        col.separator()
        
        col.operator("umap.selectmap", text="Use Selected Map", icon="RESTRICT_SELECT_OFF")


@register_class
class FetchMaps(bpy.types.Operator):
    bl_idname = "umap.listuefnmaps"
    bl_label = "List Cached UEFN Maps"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        sc = bpy.context.scene
        export_path_exists = os.path.exists(bpy.context.scene.exportPath)
        game_path_exists = os.path.exists(context.scene.Game_Path)
        return export_path_exists and game_path_exists

    def execute(self, context: Context):
        Config().dump(bpy.context.scene.exportPath)
        executable = get_exporter_executable(context)

        env_vars = os.environ.copy()
        env_vars["PATH"] = f"{context.scene.exportPath};" + env_vars["PATH"]

        result = subprocess.run(
            [executable, "--listuefnmaps"],
            executable=executable,
            capture_output=False,
            shell=False,
            check=False,
            cwd=context.scene.exportPath.replace(r"\\", "/"),
            env=env_vars,
            stdout=subprocess.PIPE,
        )

        if result.returncode == 0xC030C: # no maps found
            self.report({"WARNING"}, "No maps found.\nPlease check your config and make sure you have cached maps.")
            context.scene.uefn_maps.clear()
            return {'FINISHED'}


        if result.returncode != 0:
            if result.stdout != None:
                print(result.stdout.decode("utf-8"))
            print("Error while fetching UEFN maps:")
            if result.stderr != None:
                print(result.stderr.decode("utf-8"))
            self.report({"ERROR"}, "Error while fetching UEFN maps: see console for details")

            return {'CANCELLED'}

        output = result.stdout.decode("utf-8")

        lines = output.splitlines()
        maps = []
        maps_started = False
        for line in lines:
            if line == 'Found the following maps:':
                maps_started = True
                continue
            if not maps_started:
                continue
            if line == "":
                break
            maps.append(line.strip())

        context.scene.uefn_maps.clear()
        for _map in maps:
            context.scene.uefn_maps.add().name = _map.strip()

        return {'FINISHED'}

@register_class
class SelectMap(bpy.types.Operator):
    """set currently selected map as sc.package"""

    bl_idname = "umap.selectmap"
    bl_label = "Select Map"
    bl_description = "Set currently selected map as package in BlenderUmap panel"

    @classmethod
    def poll(cls, context):
        # # check if there are any maps
        # if len(context.scene.uefn_maps) == 0:
        #     return False
        # # check if there is a map selected
        # if context.scene.uefn_list_index == -1:
        #     return False
        # # check if the selected map is valid
        # if context.scene.uefn_list_index >= len(context.scene.uefn_maps):
        #     return False
        if not (len(context.scene.uefn_maps) > 0 and context.scene.uefn_list_index >= 0 and context.scene.uefn_list_index < len(context.scene.uefn_maps)):
            return False
        return True

    def execute(self, context: Context):
        scene = context.scene
        index = scene.uefn_list_index
        _map = scene.uefn_maps[index].name
        scene.package = _map
        return {'FINISHED'}


@register_class
class MapList(bpy.types.PropertyGroup):
    name: StringProperty(
           name="package path",
           description="relative map package path",
           default="")


@register_class
class UEFN_MAP_UL_List(bpy.types.UIList):
    """UEFN Maps List"""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        custom_icon = 'FILE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon = custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.uefn_maps = CollectionProperty(type = MapList)
    bpy.types.Scene.uefn_list_index = IntProperty(name = "index for uefn_maps", default = 0)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.uefn_maps
    del bpy.types.Scene.uefn_list_index

