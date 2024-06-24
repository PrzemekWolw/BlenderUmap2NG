import json, zlib, base64
import logging
logging.basicConfig(level=logging.DEBUG)

import sys, os
import bpy
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
os.chdir(os.path.dirname(os.path.realpath(__file__)))


# !!!! keep in sync with remote_call_manager.py
def get_blend_save_path(processed_map_path: str, data_dir) -> str:
    processed_map_path = processed_map_path.replace("\\", "/")
    if processed_map_path.startswith("/"): processed_map_path = processed_map_path[1:]

    blend_file = os.path.join(data_dir, "maps", processed_map_path+".blend")
    os.makedirs(os.path.dirname(blend_file), exist_ok=True)
    return blend_file


# function that will be called on remote process
def remote_func():
    import argparse

    parser = argparse.ArgumentParser(description="Import umap to blender")
    parser.add_argument("-j", "--umapjson", help="path to json file") # processed_map_path
    parser.add_argument("-r", "--umaproot", help="path to root folder") # data_dir
    parser.add_argument("-s", "--settings", help="settings json") # settings_json

    parsed_args = parser.parse_known_args()[0]
    # print(parser.parse_args())
    # disable all addons
    # for addon in bpy.context.preferences.addons:
    #     bpy.ops.preferences.addon_disable(module=addon.module)

    # TODO - read blenderumap config file
    bpy.context.scene.exportPath = parsed_args.umaproot
    from remote_call_manager import ImportSettings

    settings = ImportSettings(**json.loads(zlib.decompress(base64.b64decode(parsed_args.settings)).decode("utf-8")))
    sc = bpy.context.scene
    sc.reuse_maps = settings.reuse_maps
    sc.reuse_mesh = settings.reuse_meshes
    sc.use_cube_as_fallback = settings.use_cube_as_fallback
    sc.use_generic_shader = settings.use_generic_shader
    sc.use_generic_shader_as_fallback = settings.use_generic_shader_as_fallback
    sc.fallback_shader = settings.fallback_shader

    # from config.py
    for i in range(1, 5):
        for t in ["Diffuse", "Normal", "Specular", "Emission", "Mask"]:
            textures = settings.TextureMappings["UV" + str(i)][t if t != "Mask" else "MaskTexture"]
            setattr(sc, f"{t}_{i}".lower(), ",".join(textures))

    # redirect stdout to file
    loghandle = open(get_blend_save_path(parsed_args.umapjson, parsed_args.umaproot)+".log", "w")
    sys.stdout = loghandle
    sys.stderr = loghandle

    # call operator umap.onlyimport
    bpy.ops.umap.onlyimport(auto_save=False,override_processed_map_path=parsed_args.umapjson)

    # no autosave and backup
    bpy.context.preferences.filepaths.save_version = 0

    print("saving blend file")
    bpy.ops.wm.save_as_mainfile(filepath=get_blend_save_path(parsed_args.umapjson, parsed_args.umaproot))
    loghandle.close()
    print("done")

if __name__ == "__main__":
    remote_func()
    # -j thisisjsonfile -r and/this/is/roo/tfolder
