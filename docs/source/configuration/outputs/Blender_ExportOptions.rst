.. _Blender_ExportOptions:

:orphan:


Blender_ExportOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **pcb3d** :index:`: <pair: output - blender_export - options; pcb3d>`  [:ref:`PCB3DExportOptions parameters <PCB3DExportOptions>`] [:ref:`string <string>` | :ref:`dict <dict>`] (default: empty dict, default values used) Options to export the PCB to Blender.
   You can also specify the name of the output that generates the PCB3D file. |br|
   See the `PCB2Blender_2_1`, `PCB2Blender_2_7` and `PCB2Blender_2_1_haschtl` templates.
-  **point_of_view** :index:`: <pair: output - blender_export - options; point_of_view>`  [:ref:`BlenderPointOfViewOptions parameters <BlenderPointOfViewOptions>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: ``[{'view': 'top'}]``) How the object is viewed by the camera.
-  **render_options** :index:`: <pair: output - blender_export - options; render_options>`  [:ref:`BlenderRenderOptions parameters <BlenderRenderOptions>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Controls how the render is done for the `render` output type.
-  ``add_default_light`` :index:`: <pair: output - blender_export - options; add_default_light>` [:ref:`boolean <boolean>`] (default: ``true``) Add a default light when none specified.
   The default light is located at (-size*3.33, size*3.33, size*5) where size is max(width, height) of the PCB.
-  ``auto_camera_z_axis_factor`` :index:`: <pair: output - blender_export - options; auto_camera_z_axis_factor>` [:ref:`number <number>`] (default: ``1.1``) Value to multiply the Z axis coordinate after computing the automatically generated camera.
   Used to avoid collision of the camera and the object.
-  ``camera`` :index:`: <pair: output - blender_export - options; camera>`  [:ref:`BlenderCameraOptions parameters <BlenderCameraOptions>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options for the camera.
   If none specified KiBot will create a suitable camera. |br|
   If no position is specified for the camera KiBot will look for a suitable position.
-  ``default_file_id`` :index:`: <pair: output - blender_export - options; default_file_id>` [:ref:`string <string>`] (default: ``''``) Default value for the `file_id` in the `point_of_view` options.
   Use something like '_%03d' for animations.
-  ``fixed_auto_camera`` :index:`: <pair: output - blender_export - options; fixed_auto_camera>` [:ref:`boolean <boolean>`] (default: ``false``) When using the automatically generated camera and multiple points of view this option computes the camera
   position just once. Suitable for videos.
-  ``light`` :index:`: <pair: output - blender_export - options; light>`  [:ref:`BlenderLightOptions parameters <BlenderLightOptions>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: ``[{'name': 'kibot_light', 'pos_x': '-size*3.33', 'pos_y': 'size*3.33', 'pos_z': 'size*5', 'energy': 0}]``) Options for the light/s.
-  ``outputs`` :index:`: <pair: output - blender_export - options; outputs>`  [:ref:`BlenderOutputOptions parameters <BlenderOutputOptions>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: ``[{'type': 'render'}]``) Outputs to generate in the same run.
-  ``pcb_import`` :index:`: <pair: output - blender_export - options; pcb_import>`  [:ref:`PCB2BlenderOptions parameters <PCB2BlenderOptions>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options to configure how Blender imports the PCB.
   The default values are good for most cases.

Used dicts
----------

- :ref:`BlenderCameraOptions parameters <BlenderCameraOptions>`
- :ref:`BlenderLightOptions parameters <BlenderLightOptions>`
- :ref:`BlenderOutputOptions parameters <BlenderOutputOptions>`
- :ref:`BlenderPointOfViewOptions parameters <BlenderPointOfViewOptions>`
- :ref:`BlenderRenderOptions parameters <BlenderRenderOptions>`
- :ref:`PCB2BlenderOptions parameters <PCB2BlenderOptions>`
- :ref:`PCB3DExportOptions parameters <PCB3DExportOptions>`
