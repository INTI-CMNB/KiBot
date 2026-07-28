.. _Render3DOptions:

:orphan:


Render3DOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _Render3DOptions_download:

-  **download** :index:`: <pair: output - render_3d - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.

.. _Render3DOptions_move_x:

-  **move_x** :index:`: <pair: output - render_3d - options; move_x>` [:ref:`number <number>`] (default: ``0``) Steps to move in the X axis, positive is to the right.
   Just like pressing the right arrow in the 3D viewer.

.. _Render3DOptions_move_y:

-  **move_y** :index:`: <pair: output - render_3d - options; move_y>` [:ref:`number <number>`] (default: ``0``) Steps to move in the Y axis, positive is up.
   Just like pressing the up arrow in the 3D viewer.

.. _Render3DOptions_no_virtual:

-  **no_virtual** :index:`: <pair: output - render_3d - options; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.

.. _Render3DOptions_output:

-  **output** :index:`: <pair: output - render_3d - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated image file (%i='3D_$VIEW' %x='png'/'jpg'). Affected by global options.

.. _Render3DOptions_ray_tracing:

-  **ray_tracing** :index:`: <pair: output - render_3d - options; ray_tracing>` [:ref:`boolean <boolean>`] (default: ``false``) Enable the ray tracing. Much better result, but slow, and you'll need to adjust `wait_rt`.

.. _Render3DOptions_rotate_x:

-  **rotate_x** :index:`: <pair: output - render_3d - options; rotate_x>` [:ref:`number <number>`] (default: ``0``) Steps to rotate around the X axis, positive is clockwise.
   Each step is currently 10 degrees. Only for KiCad 6+.

.. _Render3DOptions_rotate_y:

-  **rotate_y** :index:`: <pair: output - render_3d - options; rotate_y>` [:ref:`number <number>`] (default: ``0``) Steps to rotate around the Y axis, positive is clockwise.
   Each step is currently 10 degrees. Only for KiCad 6+.

.. _Render3DOptions_rotate_z:

-  **rotate_z** :index:`: <pair: output - render_3d - options; rotate_z>` [:ref:`number <number>`] (default: ``0``) Steps to rotate around the Z axis, positive is clockwise.
   Each step is currently 10 degrees. Only for KiCad 6+.

.. _Render3DOptions_show_components:

-  **show_components** :index:`: <pair: output - render_3d - options; show_components>` [:ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'all'``) (choices: "none", "all") (also accepts any string) List of components to draw, can be also a string for `none` or `all`.
   Ranges like *R5-R10* are supported. |br|
   Unlike the `pcbdraw` output, the default is `all`.


.. _Render3DOptions_view:

-  **view** :index:`: <pair: output - render_3d - options; view>` [:ref:`string <string>`] (default: ``'top'``) (choices: "top", "bottom", "front", "rear", "right", "left", "z", "Z", "y", "Y", "x", "X") Point of view.

.. _Render3DOptions_zoom:

-  **zoom** :index:`: <pair: output - render_3d - options; zoom>` [:ref:`number <number>`] (default: ``0``) Zoom steps. Use positive to enlarge, get closer, and negative to reduce.
   Same result as using the mouse wheel in the 3D viewer. |br|
   Note that KiCad 8 starts with a zoom to fit, so you might not even need it.

.. _Render3DOptions_auto_crop:

-  ``auto_crop`` :index:`: <pair: output - render_3d - options; auto_crop>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled the image will be post-processed to remove the empty space around the image.
   In this mode the `background2` is changed to be the same as `background1`.

.. _Render3DOptions_background1:

-  ``background1`` :index:`: <pair: output - render_3d - options; background1>` [:ref:`string <string>`] (default: ``'#66667F'``) First color for the background gradient.

.. _Render3DOptions_background2:

-  ``background2`` :index:`: <pair: output - render_3d - options; background2>` [:ref:`string <string>`] (default: ``'#CCCCE5'``) Second color for the background gradient.

.. _Render3DOptions_board:

-  ``board`` :index:`: <pair: output - render_3d - options; board>` [:ref:`string <string>`] (default: ``'#332B16'``) Color for the board without copper or solder mask.

.. _Render3DOptions_clip_silk_on_via_annulus:

-  ``clip_silk_on_via_annulus`` :index:`: <pair: output - render_3d - options; clip_silk_on_via_annulus>` [:ref:`boolean <boolean>`] (default: ``true``) Clip silkscreen at via annuli (KiCad 6 to 9).

.. _Render3DOptions_copper:

-  ``copper`` :index:`: <pair: output - render_3d - options; copper>` [:ref:`string <string>`] (default: ``'#8b898c'``) Color for the copper, both sides.

.. _Render3DOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - render_3d - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Render3DOptions_download_lcsc:

-  ``download_lcsc`` :index:`: <pair: output - render_3d - options; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.

.. _Render3DOptions_enable_crop_workaround:

-  ``enable_crop_workaround`` :index:`: <pair: output - render_3d - options; enable_crop_workaround>` [:ref:`boolean <boolean>`] (default: ``false``) Some versions of Image Magick (i.e. the one in Debian 11) needs two passes to crop.
   Enable it to force a double pass. It was the default in KiBot 1.7.0 and older.

.. _Render3DOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - render_3d - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Render3DOptions_force_stackup_colors:

-  ``force_stackup_colors`` :index:`: <pair: output - render_3d - options; force_stackup_colors>` [:ref:`boolean <boolean>`] (default: ``false``) Tell KiCad to use the colors from the stackup. They are better than the unified KiBot colors.
   Needs KiCad 6 or newer.

.. _Render3DOptions_format:

-  ``format`` :index:`: <pair: output - render_3d - options; format>` [:ref:`string <string>`] (default: ``'png'``) (choices: "png", "jpg") Output format.

.. _Render3DOptions_height:

-  ``height`` :index:`: <pair: output - render_3d - options; height>` [:ref:`number <number>`] (default: ``720``) Image height (aprox.).

.. _Render3DOptions_highlight:

-  ``highlight`` :index:`: <pair: output - render_3d - options; highlight>` [:ref:`list(string) <list(string)>`] (default: ``[]``) List of components to highlight. Ranges like *R5-R10* are supported.


.. _Render3DOptions_highlight_on_top:

-  ``highlight_on_top`` :index:`: <pair: output - render_3d - options; highlight_on_top>` [:ref:`boolean <boolean>`] (default: ``false``) Highlight over the component (not under).

.. _Render3DOptions_highlight_padding:

-  ``highlight_padding`` :index:`: <pair: output - render_3d - options; highlight_padding>` [:ref:`number <number>`] (default: ``1.5``) (range: 0 to 1000) How much the highlight extends around the component [mm].

.. _Render3DOptions_kicad_3d_url:

-  ``kicad_3d_url`` :index:`: <pair: output - render_3d - options; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/api/v4/projects/21604637/repository/files/'``) Base URL for the KiCad 3D models.

.. _Render3DOptions_kicad_3d_url_suffix:

-  ``kicad_3d_url_suffix`` :index:`: <pair: output - render_3d - options; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``'/raw?ref=VERSION'``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.

.. _Render3DOptions_kicad_3d_url_version:

-  ``kicad_3d_url_version`` :index:`: <pair: output - render_3d - options; kicad_3d_url_version>` [:ref:`boolean <boolean>`] (default: ``true``) Replace the *master* subdir in the URL by the KiCad version.
   In this way we download the 3D model corresponding to the installed KiCad instead
   of the last available.

.. _Render3DOptions_no_smd:

-  ``no_smd`` :index:`: <pair: output - render_3d - options; no_smd>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for surface mount components.

.. _Render3DOptions_no_tht:

-  ``no_tht`` :index:`: <pair: output - render_3d - options; no_tht>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for through hole components.

.. _Render3DOptions_orthographic:

-  ``orthographic`` :index:`: <pair: output - render_3d - options; orthographic>` [:ref:`boolean <boolean>`] (default: ``false``) Enable the orthographic projection mode (top view looks flat).

.. _Render3DOptions_pivot_x:

-  ``pivot_x`` :index:`: <pair: output - render_3d - options; pivot_x>` [:ref:`number <number>`] (default: ``0``) Set pivot point relative to the board center in centimeters, X axis. Needs KiCad 10+ using CLI.

.. _Render3DOptions_pivot_y:

-  ``pivot_y`` :index:`: <pair: output - render_3d - options; pivot_y>` [:ref:`number <number>`] (default: ``0``) Set pivot point relative to the board center in centimeters, Y axis. Needs KiCad 10+ using CLI.

.. _Render3DOptions_pivot_z:

-  ``pivot_z`` :index:`: <pair: output - render_3d - options; pivot_z>` [:ref:`number <number>`] (default: ``0``) Set pivot point relative to the board center in centimeters, Z axis. Needs KiCad 10+ using CLI.

.. _Render3DOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - render_3d - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Render3DOptions_realistic:

-  ``realistic`` :index:`: <pair: output - render_3d - options; realistic>` [:ref:`boolean <boolean>`] (default: ``true``) When disabled we use the colors of the layers used by the GUI. Needs KiCad 6, 7 or 10+.
   Is emulated on KiCad 8 and 9.

.. _Render3DOptions_rotate_degrees:

-  ``rotate_degrees`` :index:`: <pair: output - render_3d - options; rotate_degrees>` [:ref:`boolean <boolean>`] (default: ``false``) Instead of `steps` use degrees for rotations. Only available for KiCad 10+ using CLI.

.. _Render3DOptions_show_adhesive:

-  ``show_adhesive`` :index:`: <pair: output - render_3d - options; show_adhesive>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of F.Adhesive/B.Adhesive layers. KiCad 6 or newer.

.. _Render3DOptions_show_board_body:

-  ``show_board_body`` :index:`: <pair: output - render_3d - options; show_board_body>` [:ref:`boolean <boolean>`] (default: ``true``) Show the PCB core material. KiCad 6 or newer.

.. _Render3DOptions_show_comments:

-  ``show_comments`` :index:`: <pair: output - render_3d - options; show_comments>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the User.Comments and User.Drawings layer for KiCad 5, 6 and 7.
   On KiCad 8+ this option controls only the User.Comments and you have a separated option for the
   User.Drawings called `show_drawings`
   Note that KiCad 5/6/7 doesn't show it when `realistic` is enabled, but KiCad 8 does it. |br|
   Also note that KiCad 5 ray tracer shows comments outside the PCB, but newer KiCad versions
   doesn't. |br|
   KiCad 10.0.3 ignores them.

.. _Render3DOptions_show_copper_bottom:

-  ``show_copper_bottom`` :index:`: <pair: output - render_3d - options; show_copper_bottom>` [:ref:`boolean <boolean>`] (default: ``true``) Show copper on the bottom layer (KiCad 10+ using CLI).

.. _Render3DOptions_show_copper_top:

-  ``show_copper_top`` :index:`: <pair: output - render_3d - options; show_copper_top>` [:ref:`boolean <boolean>`] (default: ``true``) Show copper on the top layer (KiCad 10+ using CLI).

.. _Render3DOptions_show_drawings:

-  ``show_drawings`` :index:`: <pair: output - render_3d - options; show_drawings>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the User.Drawings layer. Only available for KiCad 8 and newer.
   Consult `show_comments` to learn when drawings are visible.

.. _Render3DOptions_show_eco:

-  ``show_eco`` :index:`: <pair: output - render_3d - options; show_eco>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the Eco1.User/Eco2.User layers.
   For KiCad 8 `show_eco1` and `show_eco2` are available. |br|
   Consult `show_comments` to learn when drawings are visible.

.. _Render3DOptions_show_eco1:

-  ``show_eco1`` :index:`: <pair: output - render_3d - options; show_eco1>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the Eco1.User layer. KiCad 8 supports individual Eco layer options, for 6 and 7
   use the `show_eco` option. |br|
   Consult `show_comments` to learn when drawings are visible.

.. _Render3DOptions_show_eco2:

-  ``show_eco2`` :index:`: <pair: output - render_3d - options; show_eco2>` [:ref:`boolean <boolean>`] (default: ``false``) Show the content of the Eco1.User layer. KiCad 8 supports individual Eco layer options, for 6 and 7
   use the `show_eco` option. |br|
   Consult `show_comments` to learn when drawings are visible.

.. _Render3DOptions_show_plated_barrels:

-  ``show_plated_barrels`` :index:`: <pair: output - render_3d - options; show_plated_barrels>` [:ref:`boolean <boolean>`] (default: ``true``) Show plated through holes (KiCad 10+ using CLI).

.. _Render3DOptions_show_references:

-  ``show_references`` :index:`: <pair: output - render_3d - options; show_references>` [:ref:`boolean <boolean>`] (default: ``true``) Show component references in the silk screen (KiCad 10+ using CLI).

.. _Render3DOptions_show_silkscreen:

-  ``show_silkscreen`` :index:`: <pair: output - render_3d - options; show_silkscreen>` [:ref:`boolean <boolean>`] (default: ``true``) Show the silkscreen layers (KiCad 6+).

.. _Render3DOptions_show_soldermask:

-  ``show_soldermask`` :index:`: <pair: output - render_3d - options; show_soldermask>` [:ref:`boolean <boolean>`] (default: ``true``) Show the solder mask layers (KiCad 6+).

.. _Render3DOptions_show_solderpaste:

-  ``show_solderpaste`` :index:`: <pair: output - render_3d - options; show_solderpaste>` [:ref:`boolean <boolean>`] (default: ``true``) Show the solder paste layers (KiCad 6+).

.. _Render3DOptions_show_values:

-  ``show_values`` :index:`: <pair: output - render_3d - options; show_values>` [:ref:`boolean <boolean>`] (default: ``true``) Show component values in the silk screen (KiCad 10+ using CLI).

.. _Render3DOptions_show_zones:

-  ``show_zones`` :index:`: <pair: output - render_3d - options; show_zones>` [:ref:`boolean <boolean>`] (default: ``true``) Show filled areas in zones (KiCad 6 to 9).

.. _Render3DOptions_silk:

-  ``silk`` :index:`: <pair: output - render_3d - options; silk>` [:ref:`string <string>`] (default: ``'#d5dce4'``) Color for the silk screen, both sides.

.. _Render3DOptions_solder_mask:

-  ``solder_mask`` :index:`: <pair: output - render_3d - options; solder_mask>` [:ref:`string <string>`] (default: ``'#208b47'``) Color for the solder mask, both sides.

.. _Render3DOptions_solder_paste:

-  ``solder_paste`` :index:`: <pair: output - render_3d - options; solder_paste>` [:ref:`string <string>`] (default: ``'#808080'``) Color for the solder paste.

.. _Render3DOptions_subtract_mask_from_silk:

-  ``subtract_mask_from_silk`` :index:`: <pair: output - render_3d - options; subtract_mask_from_silk>` [:ref:`boolean <boolean>`] (default: ``true``) Clip silkscreen at solder mask edges (KiCad 6 to 9).

.. _Render3DOptions_transparent_background:

-  ``transparent_background`` :index:`: <pair: output - render_3d - options; transparent_background>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled the image will be post-processed to make the background transparent.
   In this mode the `background1` and `background2` colors are ignored. |br|
   Only available for PNGs.

.. _Render3DOptions_transparent_background_color:

-  ``transparent_background_color`` :index:`: <pair: output - render_3d - options; transparent_background_color>` [:ref:`string <string>`] (default: ``'#00ff00'``) Only used for KiCad 9 and older.
   Color used for the chroma key. Adjust it if some regions of the board becomes transparent.

.. _Render3DOptions_transparent_background_fuzz:

-  ``transparent_background_fuzz`` :index:`: <pair: output - render_3d - options; transparent_background_fuzz>` [:ref:`number <number>`] (default: ``15``) (range: 0 to 100) Chroma key tolerance (percent). Bigger values will remove more pixels.
   Only used for KiCad 9 and older.

.. _Render3DOptions_use_cli:

-  ``use_cli`` :index:`: <pair: output - render_3d - options; use_cli>` [:ref:`boolean <boolean>`] (default: ``true``) Try using `kicad-cli` for KiCad 10+. Recommended for KiCad 10.0.5 or newer.
   More reliable, but with some limitations, see KiCad bugs:
   `20126 <https://gitlab.com/kicad/code/kicad/-/work_items/20126>`__
   `24599 <https://gitlab.com/kicad/code/kicad/-/work_items/24599>`__.

.. _Render3DOptions_variant:

-  ``variant`` :index:`: <pair: output - render_3d - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

.. _Render3DOptions_wait_ray_tracing:

-  *wait_ray_tracing* :index:`: <pair: output - render_3d - options; wait_ray_tracing>` Alias for wait_render.

.. _Render3DOptions_wait_render:

-  ``wait_render`` :index:`: <pair: output - render_3d - options; wait_render>` [:ref:`number <number>`] (default: ``-600``) Only used for KiCad 9 and older.
   How many seconds we must wait before capturing the render (ray tracing or normal). |br|
   Lamentably KiCad can save an unfinished image. Enlarge it if your image looks partially rendered. |br|
   Use negative values to enable the auto-detect using CPU load. |br|
   In this case the value is interpreted as a time-out. |br|.

.. _Render3DOptions_width:

-  ``width`` :index:`: <pair: output - render_3d - options; width>` [:ref:`number <number>`] (default: ``1280``) Image width (aprox.).

