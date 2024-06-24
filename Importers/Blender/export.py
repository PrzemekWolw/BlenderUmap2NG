import bpy
import os
import json
import math
from mathutils import Vector, Matrix, Euler, Quaternion

staticObjects = []
forestItems = []
exported = []

#todo materials support
#mats = bpy.data.materials
#for mat in mats:z
  #mat.use_nodes=True
  #for x in mat.node_tree.nodes:
    #if x.type=='TEX_IMAGE':
      #x.image.file_format='PNG'
      #x.image.save_render(data_dir + '\\textures\\' + x.image.name)

class VIEW_PT_BeamExporter(bpy.types.Operator):
  """Export BeamNG"""

  bl_idname = "export.export_beamngdata"
  bl_label = "Export BeamNG data"

  def execute(self, context):
    print("Started export")
    data_dir = bpy.context.scene.exportPath
    if bpy.data.objects:
      if not os.path.exists(os.path.join(data_dir, "staticObjects")):
        os.makedirs(os.path.join(data_dir, "staticObjects"))
      with open (data_dir + '\\staticObjects\\' + 'items.level.json', 'w') as f:
        print("Exporting static objects")
        for obj in bpy.data.objects:
          if obj.type == "MESH" and obj in bpy.context.selectable_objects and not "forestItem" in obj:
            location = obj.location
            location = Euler(location, 'XYZ')
            obj.rotation_mode = 'QUATERNION'
            rotationQuat = obj.rotation_quaternion
            rotationMatrix = rotationQuat.to_matrix().transposed()
            scale = obj.scale
            name = obj.data.name
            f.write('{"class":"TSStatic","__parent":"staticObjects","position":['+ str(location[0]) + ',' + str(location[1]) + ',' + str(location[2]) + '],"rotationMatrix":[' + str(rotationMatrix[0][0]) + ',' + str(rotationMatrix[0][1]) + ',' + str(rotationMatrix[0][2]) + ',' + str(rotationMatrix[1][0]) + ',' + str(rotationMatrix[1][1]) + ',' + str(rotationMatrix[1][2]) + ',' + str(rotationMatrix[2][0]) + ',' + str(rotationMatrix[2][1]) + ',' + str(rotationMatrix[2][2]) + '],"scale":[' + str(scale[0]) + ',' + str(scale[1]) + ',' + str(scale[2]) + '],"collisionType":"None","decalType":"None","isRenderEnabled":false,"playAmbient":false,"shapeName":"/levels/nurburgring_24h/art/nurburgring_24h/staticObjects/' + str(obj.data.name) + '.dae","useInstanceRenderData":true}')
            f.write('\n')
            staticObjects.append(obj.name)
          if obj.type == "MESH" and "forestItem" in obj:
            if obj["forestItem"] == "true":
              forestItems.append(obj.name)
      if not os.path.exists(os.path.join(data_dir, "lightObjects")):
        os.makedirs(os.path.join(data_dir, "lightObjects"))
      with open (data_dir + '\\lightObjects\\' + 'items.level.json', 'w') as f:
        print("Exporting light objects")
        for obj in bpy.data.objects:
          if obj.type == "LIGHT" and obj in bpy.context.selectable_objects:
            location = obj.location
            location = Euler(location, 'XYZ')
            color = obj.data.color
            if obj.data.type == 'POINT':
              f.write('{"name":"' + str(obj.name) + '","class":"PointLight","__parent":"lightObjects","position":['+ str(location[0]) + ',' + str(location[1]) + ',' + str(location[2]) + '],"color":[' + str(color[0]) + ',' + str(color[1]) + ',' + str(color[2]) + ',1],"brightness":1,"radius":10}')
              f.write('\n')
            if obj.data.type == 'SPOT':
              rotation = obj.rotation_euler
              rotation.rotate_axis('X', math.radians(-90))
              rotationMatrix = rotation.to_matrix().transposed()
              degrees = math.degrees(obj.data.spot_size)
              f.write('{"name":"' + str(obj.name) + '","class":"SpotLight","__parent":"lightObjects","position":['+ str(location[0]) + ',' + str(location[1]) + ',' + str(location[2]) + '],"color":[' + str(color[0]) + ',' + str(color[1]) + ',' + str(color[2]) + ',1],"brightness":1,"innerAngle":5,"outerAngle":' + str(degrees) + ' ,"range":5,"rotationMatrix":[' + str(rotationMatrix[0][0]) + ',' + str(rotationMatrix[0][1]) + ',' + str(rotationMatrix[0][2]) + ',' + str(rotationMatrix[1][0]) + ',' + str(rotationMatrix[1][1]) + ',' + str(rotationMatrix[1][2]) + ',' + str(rotationMatrix[2][0]) + ',' + str(rotationMatrix[2][1]) + ',' + str(rotationMatrix[2][2]) + ']}')
              f.write('\n')

    bpy.ops.object.select_all(action='DESELECT')
    print("Exporting meshes")
    for mdl in forestItems:
      obj = bpy.data.objects[mdl]
      if not obj.data.name in exported:
        if obj.type == "MESH" and obj in bpy.context.selectable_objects:
          exported.append(obj.data.name)
          obj.select_set(True)
          if not os.path.exists(os.path.join(data_dir, "forestItems")):
            os.makedirs(os.path.join(data_dir, "forestItems"))
          exportmodel = data_dir + '\\forestItems\\' + obj.data.name + '.glb'
          if not os.path.exists(exportmodel):
            bpy.ops.export_scene.gltf(filepath = exportmodel,
                                    export_format='GLB',
                                    export_extras=True,
                                    export_draco_mesh_compression_enable=True,
                                    export_draco_mesh_compression_level=10,
                                    export_draco_position_quantization=0,
                                    export_draco_texcoord_quantization=0,
                                    export_image_format='NONE',
                                    use_selection = True)
          obj.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    for mdl in staticObjects:
      obj = bpy.data.objects[mdl]
      if not obj.data.name in exported:
        if obj.type == "MESH" and obj in bpy.context.selectable_objects:
          exported.append(obj.data.name)
          obj.select_set(True)
          if not os.path.exists(os.path.join(data_dir, "staticObjects")):
            os.makedirs(os.path.join(data_dir, "staticObjects"))
          exportmodel = data_dir + '\\staticObjects\\' + obj.data.name + '.glb'
          if not os.path.exists(exportmodel):
            bpy.ops.export_scene.gltf(filepath = exportmodel,
                                    export_format='GLB',
                                    export_extras=True,
                                    export_draco_mesh_compression_enable=True,
                                    export_draco_mesh_compression_level=10,
                                    export_draco_position_quantization=0,
                                    export_draco_texcoord_quantization=0,
                                    export_image_format='NONE',
                                    use_selection = True)
          obj.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')


    print("Done")
    return {"FINISHED"}
