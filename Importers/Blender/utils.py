import os
import sys
import bpy
from _bpy import ops

addon_dir = os.path.dirname(os.path.splitext(__file__)[0])


def get_addon_version():
    try:
        from .__version__ import __version__

        version = ".".join(__version__.split(".")[:2])
    except:
        version = "0"
    return version


def is_debug_build():
    return get_addon_version() == "0"


def get_addon_branch():
    try:
        from .__version__ import branch

        branch = branch
    except:
        branch = "debug"
    return branch


def blender_version_check_draw(layout, version=(4, 1, 0)) -> bool:
    if bpy.app.version >= version:
        layout.label(
            text="BlenderUmap2 is not compatible with Blender 4.1+", icon="ERROR"
        )
        layout.label(text="Please use Blender 4.0 or below")
        return True
    return False


def get_exporter_executable(context):
    if is_debug_build():
        exporter = os.path.abspath(
            os.path.join(
                os.path.realpath(os.path.dirname(__file__)),
                "..\\..\\BlenderUmap\\bin\\Debug\\net8.0\\BlenderUmap",
            )
        )
    else:
        exporter = os.path.join(addon_dir, "BlenderUmap")

    addon_prefs = context.preferences.addons[__package__].preferences
    if addon_prefs.filepath != "":
        exporter = addon_prefs.filepath
    if sys.platform == "win32" and not exporter.endswith(".exe"):
        executable = exporter.replace(r"\\", "/") + ".exe"
    else:
        executable = exporter.replace(r"\\", "/")

    if not os.path.exists(executable):
        print(f'"{executable}" was not found')
        raise FileNotFoundError(
            "BlenderUmap2 executable not found. make sure you have install the addon correctly"
        )
    return executable


def run_exporter(context, data_dir, args=[]):
    executable = get_exporter_executable(context)
    print(f"Running {executable} {data_dir} {' '.join(args)}")
    import subprocess

    env_vars = os.environ.copy()
    env_vars["PATH"] = f"{data_dir};" + env_vars["PATH"]

    result = subprocess.run(
        args,
        executable=executable,
        capture_output=False,
        shell=False,
        check=False,
        cwd=data_dir.replace(r"\\", "/"),
        env=env_vars,
    )

    if result.returncode != 0:
        if result.returncode == 0xE730:  # PackageNotFound
            message_box(message=f"Package not found", title="Error", icon="ERROR")
        else:
            message_box(
                message=f"BlenderUmap2 failed with exit code {result.returncode}. Check System Console (Window > Toggle System Console) for more info.",
                title="Error",
                icon="ERROR",
            )
    return result.returncode



if bpy.app.version >= (4, 0, 0):
    def shade_smooth_fast():
        return ops.call("object.shade_smooth", {})

    def wmlink_fast(filepath, directory, map_name):
        return ops.call(
                "wm.link",
                {
                    "filepath": filepath,
                    "directory": directory,
                    "filename": map_name,
                    "do_reuse_local_id": True,
                    "instance_collections": True,
                },
            )

else:
    def shade_smooth_fast():
        return ops.call("object.shade_smooth", None, {})

    def wmlink_fast(filepath, directory, map_name):
        return ops.call(
                "wm.link",
                None,
                {
                    "filepath": filepath,
                    "directory": directory,
                    "filename": map_name,
                    "do_reuse_local_id": True,
                    "instance_collections": True,
                },
            )


def message_box(message="", title="Message Box", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
