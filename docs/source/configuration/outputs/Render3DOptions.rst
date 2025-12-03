.. _Render3DOptions:

:orphan:


Render3DOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **download** :index:`: <pair: output - render_3d - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.
-  **move_x** :index:`: <pair: output - render_3d - options; move_x>` [:ref:`number <number>`] (default: ``0``) Steps to move in the X axis, positive is to the right.
   Just like pressing the right arrow in the 3D viewer.
-  **move_y** :index:`: <pair: output - render_3d - options; move_y>` [:ref:`number <number>`] (default: ``0``) Steps to move in the Y axis, positive is up.
   Just like pressing the up arrow in the 3D viewer.
-  **no_virtual** :index:`: <pair: output - render_3d - options; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.
-  **output** :index:`: <pair: output - render_3d - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated image file (%i='3D_$VIEW' %x='png'). Affected by global options.
-  **ray_tracing** :index:`: <pair: output - render_3d - options; ray_tracing>` [:ref:`boolean <boolean>`] (default: ``false``) Enable the ray tracing. Much better result, but slow, and you'll need to adjust `wait_rt`.
-  **rotate_x** :index:`: <pair: output - render_3d - options; rotate_x>` [:ref:`number <number>`] (default: ``0``) Steps to rotate around the X axis, positive is clockwise.
   Each step is currently 10 degrees. Only for KiCad 6 or newer.
-  **rotate_y** :index:`: <pair: output - render_3d - options; rotate_y>` [:ref:`number <number>`] (default: ``0``) Steps to rotate around the Y axis, positive is clockwise.
   Each step is currently 10 degrees. Only for KiCad 6 or newer.
-  **rotate_z** :index:`: <pair: output - render_3d - options; rotate_z>` [:ref:`number <number>`] (default: ``0``) Steps to rotate around the Z axis, positive is clockwise.
   Each step is currently 10 degrees. Only for KiCad 6 or newer.
-  **show_components** :index:`: <pair: output - render_3d - options; show_components>` [:ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'all'``) (choices: "none", "all") (also accepts any string) List of components to draw, can be also a string for `none` or `all`.
   Ranges like *R5-R10* are supported. |br|
   Unlike the `pcbdraw` output, the default is `all`.

-  **view** :index:`: <pair: output - render_3d - options; view>` [:ref:`string <string>`] (default: ``'top'``) (choices: "top", "bottom", "front", "rear", "right", "left", "z", "Z", "y", "Y", "x", "X") Point of view.
-  **zoom** :index:`: <pair: output - render_3d - options; zoom>` [:ref:`number <number>`] (default: ``0``) Zoom steps. Use positive to enlarge, get closer, and negative to reduce.
   Same result as using the mouse wheel in the 3D viewer. |br|
   Note that KiCad 8 starts with a zoom to fit, so you might not even need it.
-  ``auto_crop`` :index:`: <pair: output - render_3d - options; auto_crop>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled the image will be post-processed to remove the empty space around the image.
   In this mode the `background2` is changed to be the same as `background1`.
-  ``background1`` :index:`: <pair: output - render_3d - options; background1>` [:ref:`string <string>`] (default: ``'#66667F'``) First color for the background gradient.
-  ``background2`` :index:`: <pair: output - render_3d - options; background2>` [:ref:`string <string>`] (default: ``'#CCCCE5'``) Second color for the background gradient.
-  ``board`` :index:`: <pair: output - render_3d - options; board>` [:ref:`string <string>`] (default: ``'#332B16'``) Color for the board without copper or solder mask.
-  ``clip_silk_on_via_annulus`` :index:`: <pair: output - render_3d - options; clip_silk_on_via_annulus>` [:ref:`boolean <boolean>`] (default: ``true``) Clip silkscreen at via annuli (KiCad 6+).
-  ``copper`` :index:`: <pair: output - render_3d - options; copper>` [:ref:`string <string>`] (default: ``'#8b898c'``) Color for the copper.
-  ``dnf_filter`` :index:`: <pair: output - render_3d - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``download_lcsc`` :index:`: <pair: output - render_3d - options; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.
-  ``enable_crop_workaround`` :index:`: <pair: output - render_3d - options; enable_crop_workaround>` [:ref:`boolean <boolean>`] (default: ``false``) Some versions of Image Magick (i.e. the one in Debian 11) needs two passes to crop.
   Enable it to force a double pass. It was the default in KiBot 1.7.0 and older.
-  ``exclude_filter`` :index:`: <pair: output - render_3d - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``force_stackup_colors`` :index:`: <pair: output - render_3d - options; force_stackup_colors>` [:ref:`boolean <boolean>`] (default: ``false``) Tell KiCad to use the colors from the stackup. They are better than the unified KiBot colors.
   Needs KiCad 6 or newer.
-  ``height`` :index:`: <pair: output - render_3d - options; height>` [:ref:`number <number>`] (default: ``720``) Image height (aprox.).
-  ``highlight`` :index:`: <pair: output - render_3d - options; highlight>` [:ref:`list(string) <list(string)>`] (default: ``[]``) List of components to highlight. Ranges like *R5-R10* are supported.

-  ``highlight_on_top`` :index:`: <pair: output - render_3d - options; highlight_on_top>` [:ref:`boolean <boolean>`] (default: ``false``) Highlight over the component (not under).
-  ``highlight_padding`` :index:`: <pair: output - render_3d - options; highlight_padding>` [:ref:`number <number>`] (default: ``1.5``) (range: 0 to 1000) How much the highlight extends around the component [mm].
-  ``kicad_3d_url`` :index:`: <pair: output - render_3d - options; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'``) Base URL for the KiCad 3D models.
-  ``kicad_3d_url_suffix`` :index:`: <pair: output - render_3d - options; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``''``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.
-  ``no_smd`` :index:`: <pair: output - render_3d - options; no_smd>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for surface mount components.
-  ``no_tht`` :index:`: <pair: output - render_3d - options; no_tht>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for through hole components.
-  ``orthographic`` :index:`: <pair: output - render_3d - options; orthographic>` [:ref:`boolean <boolean>`] (default: ``false``) Enable the orthographic projection mode (top view looks flat).
-  ``pre_transform`` :index:`: <pair: output - render_3d - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``realistic`` :index:`: <pair: output - render_3d - options; realistic>` [:ref:`boolean <boolean>`] (default: ``true``) When disabled we use the colors of the layers used by the GUI. Needs KiCad 6 or 7.
   Is emulated on KiCad 8.
-  ``show_adhesive`` :index:`: <pair: output - render_3d - options; show_adhesive>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of F.Adhesive/B.Adhesive layers. KiCad 6 or newer.
-  ``show_board_body`` :index:`: <pair: output - render_3d - options; show_board_body>` [:ref:`boolean <boolean>`] (default: ``true``) Show the PCB core material. KiCad 6 or newer.
-  ``show_comments`` :index:`: <pair: output - render_3d - options; show_comments>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the User.Comments and User.Drawings layer for KiCad 5, 6 and 7.
   On KiCad 8 this option controls only the User.Comments and you have a separated option for the
   User.Drawings called `show_drawings`
   Note that KiCad 5/6/7 doesn't show it when `realistic` is enabled, but KiCad 8 does it. |br|
   Also note that KiCad 5 ray tracer shows comments outside the PCB, but newer KiCad versions
   doesn't.
-  ``show_drawings`` :index:`: <pair: output - render_3d - options; show_drawings>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the User.Drawings layer. Only available for KiCad 8 and newer.
   Consult `show_comments` to learn when drawings are visible.
-  ``show_eco`` :index:`: <pair: output - render_3d - options; show_eco>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the Eco1.User/Eco2.User layers.
   For KiCad 8 `show_eco1` and `show_eco2` are available. |br|
   Consult `show_comments` to learn when drawings are visible.
-  ``show_eco1`` :index:`: <pair: output - render_3d - options; show_eco1>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the Eco1.User layer. KiCad 8 supports individual Eco layer options, for 6 and 7
   use the `show_eco` option. |br|
   Consult `show_comments` to learn when drawings are visible.
-  ``show_eco2`` :index:`: <pair: output - render_3d - options; show_eco2>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the Eco1.User layer. KiCad 8 supports individual Eco layer options, for 6 and 7
   use the `show_eco` option. |br|
   Consult `show_comments` to learn when drawings are visible.
-  ``show_silkscreen`` :index:`: <pair: output - render_3d - options; show_silkscreen>` [:ref:`boolean <boolean>`] (default: ``true``) Show the silkscreen layers (KiCad 6+).
-  ``show_soldermask`` :index:`: <pair: output - render_3d - options; show_soldermask>` [:ref:`boolean <boolean>`] (default: ``true``) Show the solder mask layers (KiCad 6+).
-  ``show_solderpaste`` :index:`: <pair: output - render_3d - options; show_solderpaste>` [:ref:`boolean <boolean>`] (default: ``true``) Show the solder paste layers (KiCad 6+).
-  ``show_zones`` :index:`: <pair: output - render_3d - options; show_zones>` [:ref:`boolean <boolean>`] (default: ``true``) Show filled areas in zones (KiCad 6+).
-  ``silk`` :index:`: <pair: output - render_3d - options; silk>` [:ref:`string <string>`] (default: ``'#d5dce4'``) Color for the silk screen.
-  ``solder_mask`` :index:`: <pair: output - render_3d - options; solder_mask>` [:ref:`string <string>`] (default: ``'#208b47'``) Color for the solder mask.
-  ``solder_paste`` :index:`: <pair: output - render_3d - options; solder_paste>` [:ref:`string <string>`] (default: ``'#808080'``) Color for the solder paste.
-  ``subtract_mask_from_silk`` :index:`: <pair: output - render_3d - options; subtract_mask_from_silk>` [:ref:`boolean <boolean>`] (default: ``true``) Clip silkscreen at solder mask edges (KiCad 6+).
-  ``transparent_background`` :index:`: <pair: output - render_3d - options; transparent_background>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled the image will be post-processed to make the background transparent.
   In this mode the `background1` and `background2` colors are ignored.
-  ``transparent_background_color`` :index:`: <pair: output - render_3d - options; transparent_background_color>` [:ref:`string <string>`] (default: ``'#00ff00'``) Color used for the chroma key. Adjust it if some regions of the board becomes transparent.
-  ``transparent_background_fuzz`` :index:`: <pair: output - render_3d - options; transparent_background_fuzz>` [:ref:`number <number>`] (default: ``15``) (range: 0 to 100) Chroma key tolerance (percent). Bigger values will remove more pixels.
-  ``variant`` :index:`: <pair: output - render_3d - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
-  *wait_ray_tracing* :index:`: <pair: output - render_3d - options; wait_ray_tracing>` Alias for wait_render.
-  ``wait_render`` :index:`: <pair: output - render_3d - options; wait_render>` [:ref:`number <number>`] (default: ``-600``) How many seconds we must wait before capturing the render (ray tracing or normal).
   Lamentably KiCad can save an unfinished image. Enlarge it if your image looks partially rendered. |br|
   Use negative values to enable the auto-detect using CPU load. |br|
   In this case the value is interpreted as a time-out. |br|.
-  ``width`` :index:`: <pair: output - render_3d - options; width>` [:ref:`number <number>`] (default: ``1280``) Image width (aprox.).

