.. _BlenderPointOfViewOptions:

:orphan:


BlenderPointOfViewOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **view** :index:`: <pair: output - blender_export - options - point_of_view; view>` [:ref:`string <string>`] (default: ``'top'``) (choices: "top", "bottom", "front", "rear", "right", "left", "z", "Z", "y", "Y", "x", "X") Point of view.
   Compatible with `render_3d`.
-  ``file_id`` :index:`: <pair: output - blender_export - options - point_of_view; file_id>` [:ref:`string <string>`] (default: ``''``) String to differentiate the name of this point of view.
   When empty we use the `default_file_id` or the `view`.
-  ``rotate_x`` :index:`: <pair: output - blender_export - options - point_of_view; rotate_x>` [:ref:`number <number>`] (default: ``0``) Angle to rotate the board in the X axis, positive is clockwise [degrees].
-  ``rotate_y`` :index:`: <pair: output - blender_export - options - point_of_view; rotate_y>` [:ref:`number <number>`] (default: ``0``) Angle to rotate the board in the Y axis, positive is clockwise [degrees].
-  ``rotate_z`` :index:`: <pair: output - blender_export - options - point_of_view; rotate_z>` [:ref:`number <number>`] (default: ``0``) Angle to rotate the board in the Z axis, positive is clockwise [degrees].
-  ``steps`` :index:`: <pair: output - blender_export - options - point_of_view; steps>` [:ref:`number <number>`] (default: ``1``) (range: 1 to 1000) Generate this amount of steps using the rotation angles as increments.
   Use a value of 1 (default) to interpret the angles as absolute. |br|
   Used for animations. You should define the `default_file_id` to something like
   '_%03d' to get the animation frames.

