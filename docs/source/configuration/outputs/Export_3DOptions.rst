.. _Export_3DOptions:

:orphan:


Export_3DOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **download** :index:`: <pair: output - export_3d - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.
-  **format** :index:`: <pair: output - export_3d - options; format>` [:ref:`string <string>`] (default: ``'step'``) (choices: "step", "glb", "stl", "xao", "brep") 3D format used.

   - STEP: ISO 10303-21 Clear Text Encoding of the Exchange Structure
   - GLB: Binary version of the glTF, Graphics Library Transmission Format or GL Transmission Format and formerly

   known as WebGL Transmissions Format or WebGL TF. |br|

   - STL: 3D printer format, from stereolithography CAD software created by 3D Systems. |br|
   - XAO: XAO (SALOME/Gmsh) format, used for FEM and simulations. |br|
   - BRep: Part of Open CASCADE Technology (OCCT).
-  **no_virtual** :index:`: <pair: output - export_3d - options; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.
-  **origin** :index:`: <pair: output - export_3d - options; origin>` [:ref:`string <string>`] (default: ``'grid'``) (choices: "grid", "drill", "center") (also accepts any string) Determines the coordinates origin.
   Using `grid` the coordinates are the same as you have in the design sheet. |br|
   The `drill` option uses the auxiliary reference defined by the user. |br|
   Using `center` you'll get the center of the board as origin. |br|
   You can define any other origin using the format 'X,Y', i.e. '3.2,-10'. Don't put units here. |br|
   The units used here are the ones specified by the `units` option.
-  **output** :index:`: <pair: output - export_3d - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated 3D file (%i='3D' %x='step/glb/stl/xao/brep'). Affected by global options.
-  ``board_only`` :index:`: <pair: output - export_3d - options; board_only>` [:ref:`boolean <boolean>`] (default: ``false``) Only generate a board with no components.
-  ``cut_vias_in_body`` :index:`: <pair: output - export_3d - options; cut_vias_in_body>` [:ref:`boolean <boolean>`] (default: ``false``) Cut via holes in board body even if conductor layers are not exported.
-  ``dnf_filter`` :index:`: <pair: output - export_3d - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``download_lcsc`` :index:`: <pair: output - export_3d - options; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.
-  ``exclude_filter`` :index:`: <pair: output - export_3d - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``fill_all_vias`` :index:`: <pair: output - export_3d - options; fill_all_vias>` [:ref:`boolean <boolean>`] (default: ``false``) Don't cut via holes in conductor layers.
-  ``fuse_shapes`` :index:`: <pair: output - export_3d - options; fuse_shapes>` [:ref:`boolean <boolean>`] (default: ``false``) Fuse overlapping geometry together.
-  ``include_inner_copper`` :index:`: <pair: output - export_3d - options; include_inner_copper>` [:ref:`boolean <boolean>`] (default: ``false``) Export elements on inner copper layers.
-  ``include_pads`` :index:`: <pair: output - export_3d - options; include_pads>` [:ref:`boolean <boolean>`] (default: ``false``) Export pads.
-  ``include_silkscreen`` :index:`: <pair: output - export_3d - options; include_silkscreen>` [:ref:`boolean <boolean>`] (default: ``false``) Export silkscreen graphics as a set of flat faces.
-  ``include_soldermask`` :index:`: <pair: output - export_3d - options; include_soldermask>` [:ref:`boolean <boolean>`] (default: ``false``) Export soldermask layers as a set of flat faces.
-  ``include_tracks`` :index:`: <pair: output - export_3d - options; include_tracks>` [:ref:`boolean <boolean>`] (default: ``false``) Export tracks and vias.
-  ``include_zones`` :index:`: <pair: output - export_3d - options; include_zones>` [:ref:`boolean <boolean>`] (default: ``false``) Export zones.
-  ``kicad_3d_url`` :index:`: <pair: output - export_3d - options; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'``) Base URL for the KiCad 3D models.
-  ``kicad_3d_url_suffix`` :index:`: <pair: output - export_3d - options; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``''``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.
-  ``kicad_3d_url_version`` :index:`: <pair: output - export_3d - options; kicad_3d_url_version>` [:ref:`boolean <boolean>`] (default: ``true``) Replace the *master* subdir in the URL by the KiCad version.
   In this way we download the 3D model corresponding to the installed KiCad instead
   of the last available.
-  ``min_distance`` :index:`: <pair: output - export_3d - options; min_distance>` [:ref:`number <number>`] (default: ``-1``) The minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm).
   The units for this option are controlled by the `units` option.
-  ``net_filter`` :index:`: <pair: output - export_3d - options; net_filter>` [:ref:`string <string>`] (default: ``''``) Only include copper items belonging to nets matching this wildcard.
-  ``no_board_body`` :index:`: <pair: output - export_3d - options; no_board_body>` [:ref:`boolean <boolean>`] (default: ``false``) Exclude board body.
-  ``no_components`` :index:`: <pair: output - export_3d - options; no_components>` [:ref:`boolean <boolean>`] (default: ``false``) Exclude 3D models for components.
-  ``no_optimize_step`` :index:`: <pair: output - export_3d - options; no_optimize_step>` [:ref:`boolean <boolean>`] (default: ``false``) Do not optimize STEP file (enables writing parametric curves).
-  ``pre_transform`` :index:`: <pair: output - export_3d - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``subst_models`` :index:`: <pair: output - export_3d - options; subst_models>` [:ref:`boolean <boolean>`] (default: ``true``) Substitute STEP or IGS models with the same name in place of VRML models.
-  ``units`` :index:`: <pair: output - export_3d - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches", "mils") Units used for the custom origin and `min_distance`. Affected by global options.
-  ``variant`` :index:`: <pair: output - export_3d - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

