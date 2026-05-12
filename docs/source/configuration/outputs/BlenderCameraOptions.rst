.. _BlenderCameraOptions:

:orphan:


BlenderCameraOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``clip_start`` :index:`: <pair: output - blender_export - options - camera; clip_start>` [:ref:`number <number>`] (default: ``-1``) Minimum distance for objects to the camera. Any object closer than this distance won't be visible.
   Only positive values have effect. A negative value has a special meaning. |br|
   For a camera with defined position, a negative value means to use Blender defaults (i.e. 0.1 m). |br|
   For cameras without position KiBot will ask Blender to compute its position and the use a clip
   distance that is 1/10th of the Z distance.
-  ``name`` :index:`: <pair: output - blender_export - options - camera; name>` [:ref:`string <string>`] (default: ``''``) Name for the camera.
-  ``pos_x`` :index:`: <pair: output - blender_export - options - camera; pos_x>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) X position [m]. You can use `width`, `height` and `size` for PCB dimensions.
-  ``pos_y`` :index:`: <pair: output - blender_export - options - camera; pos_y>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Y position [m]. You can use `width`, `height` and `size` for PCB dimensions.
-  ``pos_z`` :index:`: <pair: output - blender_export - options - camera; pos_z>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Z position [m]. You can use `width`, `height` and `size` for PCB dimensions.
-  **type** :index:`: <pair: output - blender_export - options - camera; type>` ''

