.. _BlenderRenderOptions:

:orphan:


BlenderRenderOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _BlenderRenderOptions_samples:

-  **samples** :index:`: <pair: output - blender_export - options - render_options; samples>` [:ref:`number <number>`] (default: ``10``) How many samples we create. Each sample is a raytracing render.
   Use 1 for a raw preview, 10 for a draft and 100 or more for the final render.

.. _BlenderRenderOptions_transparent_background:

-  **transparent_background** :index:`: <pair: output - blender_export - options - render_options; transparent_background>` [:ref:`boolean <boolean>`] (default: ``false``) Make the background transparent.

.. _BlenderRenderOptions_auto_crop:

-  ``auto_crop`` :index:`: <pair: output - blender_export - options - render_options; auto_crop>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled the image will be post-processed to remove the empty space around the image.
   In this mode the `background2` is changed to be the same as `background1`.

.. _BlenderRenderOptions_background1:

-  ``background1`` :index:`: <pair: output - blender_export - options - render_options; background1>` [:ref:`string <string>`] (default: ``'#66667F'``) First color for the background gradient.

.. _BlenderRenderOptions_background2:

-  ``background2`` :index:`: <pair: output - blender_export - options - render_options; background2>` [:ref:`string <string>`] (default: ``'#CCCCE5'``) Second color for the background gradient.

.. _BlenderRenderOptions_height:

-  *height* :index:`: <pair: output - blender_export - options - render_options; height>` Alias for resolution_y.

.. _BlenderRenderOptions_no_denoiser:

-  ``no_denoiser`` :index:`: <pair: output - blender_export - options - render_options; no_denoiser>` [:ref:`boolean <boolean>`] (default: ``false``) Used to disable the render denoiser on old hardware, or when the functionality isn't compiled.
   Note that the impact in quality is huge, you should increase the amount of samples 10 times.

.. _BlenderRenderOptions_resolution_x:

-  ``resolution_x`` :index:`: <pair: output - blender_export - options - render_options; resolution_x>` [:ref:`number <number>`] (default: ``1280``) Width of the image.

.. _BlenderRenderOptions_resolution_y:

-  ``resolution_y`` :index:`: <pair: output - blender_export - options - render_options; resolution_y>` [:ref:`number <number>`] (default: ``720``) Height of the image.

.. _BlenderRenderOptions_width:

-  *width* :index:`: <pair: output - blender_export - options - render_options; width>` Alias for resolution_x.

