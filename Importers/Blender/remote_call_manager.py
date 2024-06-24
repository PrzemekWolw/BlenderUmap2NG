import bpy
import os
import subprocess
import multiprocessing
import json, zlib, base64
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time
import ctypes

from _bpy import ops


if bpy.app.version >= (4, 0, 0):
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


class PERFORMANCE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("CommitTotal", ctypes.c_size_t),
        ("CommitLimit", ctypes.c_size_t),
        ("CommitPeak", ctypes.c_size_t),
        ("PhysicalTotal", ctypes.c_size_t),
        ("PhysicalAvailable", ctypes.c_size_t),
        ("SystemCache", ctypes.c_size_t),
        ("KernelTotal", ctypes.c_size_t),
        ("KernelPaged", ctypes.c_size_t),
        ("KernelNonpaged", ctypes.c_size_t),
        ("PageSize", ctypes.c_size_t),
        ("HandleCount", ctypes.c_ulong),
        ("ProcessCount", ctypes.c_ulong),
        ("ThreadCount", ctypes.c_ulong),
    ]


def get_windows_ram_info():
    perf_info = PERFORMANCE_INFORMATION()

    perf_info.cb = ctypes.sizeof(perf_info)

    if ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(perf_info), perf_info.cb):
        return (perf_info.PhysicalTotal * perf_info.PageSize) // 1024**2, (
            perf_info.PhysicalAvailable * perf_info.PageSize
        ) // 1024**2
    else:
        return None, None


def determine_max_processes() -> int:
    # determine max processes based on system specs
    # 1 process per thread or 1 process per gb of empty ram
    # whichever is lower and we reserve 10% of the total ram

    cpu_cores = multiprocessing.cpu_count()
    import sys

    if sys.platform != "win32":
        return cpu_cores

    total_ram, available_ram = get_windows_ram_info()
    processes_based_on_cores = min(cpu_cores, available_ram)

    # Reserve 10% of the total RAM
    reserved_ram = int(total_ram * 0.1)
    available_ram_after_reservation = max(0, total_ram - reserved_ram)

    processes_based_on_ram = min(
        cpu_cores, int(available_ram_after_reservation / 1024)
    )  # 1 process per GB
    max_processes = min(processes_based_on_cores, processes_based_on_ram)

    return max(max_processes, 1)


@dataclass
class ImportSettings:
    reuse_maps: bool
    reuse_meshes: bool
    use_cube_as_fallback: bool
    use_generic_shader: bool
    use_generic_shader_as_fallback: bool
    fallback_shader: str
    TextureMappings: list


# keep in sync with remote_call.py
# can be imported from remote_call.py?
def get_blend_save_path(processed_map_path: str, data_dir) -> str:
    processed_map_path = processed_map_path.replace("\\", "/")
    if processed_map_path.startswith("/"):
        processed_map_path = processed_map_path[1:]

    blend_file = os.path.join(data_dir, "maps", processed_map_path + ".blend")
    os.makedirs(os.path.dirname(blend_file), exist_ok=True)
    # print("remote_call.py: get_blend_save_path()", blend_file)
    return blend_file


def process_child_comp(maps, data_dir, into_collection: "bpy.types.Collection"):
    # TODO: temp dump config.json for only import use cases

    blender_exe = bpy.app.binary_path

    MAX_PROCESSES = determine_max_processes()

    # get current py file_path
    py_file_path = os.path.dirname(os.path.realpath(__file__))
    py_file_path = py_file_path.replace("\\", "/")
    py_file_path = os.path.join(py_file_path, "remote_call.py")

    from .texture import textures_to_mapping

    sc = bpy.context.scene
    settings = ImportSettings(
        reuse_maps=sc.reuse_maps,
        reuse_meshes=sc.reuse_mesh,
        use_cube_as_fallback=sc.use_cube_as_fallback,
        use_generic_shader=sc.use_generic_shader,
        use_generic_shader_as_fallback=sc.use_generic_shader_as_fallback,
        fallback_shader=sc.fallback_shader,
        TextureMappings=textures_to_mapping(sc).to_dict(),
    )

    # prepare settings to be passed to remote_call.py as arguments as base64 encoded json

    settings_json = json.dumps(settings.__dict__)
    settings_json = settings_json.encode("utf-8")
    settings_json = zlib.compress(settings_json)
    settings_json = base64.b64encode(settings_json)

    # for umap in maps:
    def threadFunc(umap):
        blend_path = get_blend_save_path(umap, data_dir)

        if (
            bpy.context.scene.reuse_maps
            and os.path.exists(blend_path)
            and os.path.getsize(blend_path) > 0
        ):
            # print("skipping map", umap, "already exists")
            return (umap, blend_path)

        process = subprocess.Popen(
            [
                blender_exe,
                "--background",
                "--python",
                py_file_path,
                "--umapjson",
                umap,
                "--umaproot",
                data_dir,
                "--settings",
                settings_json,
            ]
        )
        print("spawned process for map", " ".join([str(arg) for arg in process.args]))
        process.wait()
        # assert process.returncode == 0, f"failed to import map {umap} \n {process.stdout}"

        return (umap, blend_path)

    # maps = [x for x in maps if x.endswith("7S74EY2P5IDHKXJ2OKSZ7TXAN")]
    # TODO: queue large maps first

    t_index = 0  # map index to keep track of which map we are currently processing
    futures = []
    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() + 1) as executor:
        # dynamically submit tasks based on determined max processes
        while True:
            new_process_count = determine_max_processes()
            if t_index >= len(maps):
                break
            # get number of running processes from future objects
            running_processes = len([x for x in futures if x.running()])

            # running_threads = len([x for x in executor._threads if x.is_alive()])

            if running_processes < new_process_count:
                # print(f" submitting map {t_index} of {len(maps)} to thread pool because {running_threads}({running_processes=}) < {new_process_count=}")
                task = executor.submit(threadFunc, maps[t_index])
                futures.append(task)
                time.sleep(
                    0.01
                )  # wait a bit to give the thread pool time to start the task
                t_index += 1
            else:
                # print(f" waiting for thread pool to finish processing maps because {running_processes=} >= {new_process_count=}")
                time.sleep(0.1)
                continue

        # results = list(executor.map(threadFunc, maps))

    while True:
        running_processes = len([x for x in executor._threads if x.is_alive()])
        if running_processes == 0:
            break
        print(
            f" waiting for thread pool to finish processing maps {running_processes=}"
        )
        time.sleep(0.1)

    results = [x.result() for x in futures]

    assert bpy.ops.wm.link.poll(), "linking not possible"
    # no linking allowed on non main thread apparently
    objs = []
    for i, x in enumerate(results):
        print(f"Linked map {i} of {len(results)}: {x[0]}")

        blend_file = x[1]

        sec = "\\Collection\\"
        map_name = x[0][x[0].rindex("/") + 1 :]  # collection name

        filepath = blend_file + sec + map_name
        directory = blend_file + sec

        assert os.path.exists(blend_file), blend_file + " does not exist"

        coll = bpy.data.collections.get(map_name)

        if coll is None:
            wmlink_fast(filepath, directory, map_name)

            coll = bpy.data.collections.get(map_name)

            spawned_one = (
                bpy.context.view_layer.active_layer_collection.collection.objects.get(
                    coll.name
                )
            )
            if spawned_one is not None:
                bpy.context.view_layer.active_layer_collection.collection.objects.unlink(
                    spawned_one
                )

            def place_map(
                collection: bpy.types.Collection, into_collection: bpy.types.Collection
            ):  # same as umap.py.place_map
                c_inst = bpy.data.objects.new(collection.name, None)
                c_inst.instance_type = "COLLECTION"
                c_inst.instance_collection = collection
                into_collection.objects.link(c_inst)
                return c_inst

            obj = place_map(coll, into_collection)
            objs.append(obj)
            continue

    return objs
