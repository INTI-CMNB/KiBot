.. _Export_3DOptions:

:orphan:


Export_3DOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _Export_3DOptions_download:

-  **download** :index:`: <pair: output - export_3d - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.

.. _Export_3DOptions_format:

-  **format** :index:`: <pair: output - export_3d - options; format>` [:ref:`string <string>`] (default: ``'step'``) (choices: "step", "glb", "stl", "xao", "brep", "ply", "u3d", "pdf") 3D format used.

   - STEP: ISO 10303-21 Clear Text Encoding of the Exchange Structure
   - GLB: Binary version of the glTF, Graphics Library Transmission Format or GL Transmission Format and formerly
     known as WebGL Transmissions Format or WebGL TF. |br|
   - STL: 3D printer format, from stereolithography CAD software created by 3D Systems. |br|
   - XAO: XAO (SALOME/Gmsh) format, used for FEM and simulations. |br|
   - BRep: Part of Open CASCADE Technology (OCCT)
   - PLY: Polygon File Format or the Stanford Triangle Format (KiCad 10+). |br|
   - U3D: Universal 3D (ECMA-363) primarily used to embed interactive 3D models into PDF documents. (KiCad 10+)
   - PDF: Portable Document Format with the 3D model (KiCad 10+).

.. _Export_3DOptions_no_virtual:

-  **no_virtual** :index:`: <pair: output - export_3d - options; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.

.. _Export_3DOptions_origin:

-  **origin** :index:`: <pair: output - export_3d - options; origin>` [:ref:`string <string>`] (default: ``'grid'``) (choices: "grid", "drill", "center") (also accepts any string) Determines the coordinates origin.
   Using `grid` the coordinates are the same as you have in the design sheet. |br|
   The `drill` option uses the auxiliary reference defined by the user. |br|
   Using `center` you'll get the center of the board as origin. |br|
   You can define any other origin using the format 'X,Y', i.e. '3.2,-10'. Don't put units here. |br|
   The units used here are the ones specified by the `units` option.

.. _Export_3DOptions_output:

-  **output** :index:`: <pair: output - export_3d - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated 3D file (%i='3D' %x='step/glb/stl/xao/brep/ply/u3d/pdf'). Affected by global options.

.. _Export_3DOptions_board_only:

-  ``board_only`` :index:`: <pair: output - export_3d - options; board_only>` [:ref:`boolean <boolean>`] (default: ``false``) Only generate a board with no components.

.. _Export_3DOptions_cut_vias_in_body:

-  ``cut_vias_in_body`` :index:`: <pair: output - export_3d - options; cut_vias_in_body>` [:ref:`boolean <boolean>`] (default: ``false``) Cut via holes in board body even if conductor layers are not exported.

.. _Export_3DOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - export_3d - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Export_3DOptions_download_lcsc:

-  ``download_lcsc`` :index:`: <pair: output - export_3d - options; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.

.. _Export_3DOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - export_3d - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Export_3DOptions_fill_all_vias:

-  ``fill_all_vias`` :index:`: <pair: output - export_3d - options; fill_all_vias>` [:ref:`boolean <boolean>`] (default: ``false``) Don't cut via holes in conductor layers.

.. _Export_3DOptions_fuse_shapes:

-  ``fuse_shapes`` :index:`: <pair: output - export_3d - options; fuse_shapes>` [:ref:`boolean <boolean>`] (default: ``false``) Fuse overlapping geometry together.

.. _Export_3DOptions_include_inner_copper:

-  ``include_inner_copper`` :index:`: <pair: output - export_3d - options; include_inner_copper>` [:ref:`boolean <boolean>`] (default: ``false``) Export elements on inner copper layers.

.. _Export_3DOptions_include_pads:

-  ``include_pads`` :index:`: <pair: output - export_3d - options; include_pads>` [:ref:`boolean <boolean>`] (default: ``false``) Export pads.

.. _Export_3DOptions_include_silkscreen:

-  ``include_silkscreen`` :index:`: <pair: output - export_3d - options; include_silkscreen>` [:ref:`boolean <boolean>`] (default: ``false``) Export silkscreen graphics as a set of flat faces.

.. _Export_3DOptions_include_soldermask:

-  ``include_soldermask`` :index:`: <pair: output - export_3d - options; include_soldermask>` [:ref:`boolean <boolean>`] (default: ``false``) Export soldermask layers as a set of flat faces.

.. _Export_3DOptions_include_tracks:

-  ``include_tracks`` :index:`: <pair: output - export_3d - options; include_tracks>` [:ref:`boolean <boolean>`] (default: ``false``) Export tracks and vias.

.. _Export_3DOptions_include_zones:

-  ``include_zones`` :index:`: <pair: output - export_3d - options; include_zones>` [:ref:`boolean <boolean>`] (default: ``false``) Export zones.

.. _Export_3DOptions_kicad_3d_url:

-  ``kicad_3d_url`` :index:`: <pair: output - export_3d - options; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/api/v4/projects/21604637/repository/files/'``) Base URL for the KiCad 3D models.

.. _Export_3DOptions_kicad_3d_url_suffix:

-  ``kicad_3d_url_suffix`` :index:`: <pair: output - export_3d - options; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``'/raw?ref=VERSION'``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.

.. _Export_3DOptions_kicad_3d_url_version:

-  ``kicad_3d_url_version`` :index:`: <pair: output - export_3d - options; kicad_3d_url_version>` [:ref:`boolean <boolean>`] (default: ``true``) Replace the *master* subdir in the URL by the KiCad version.
   In this way we download the 3D model corresponding to the installed KiCad instead
   of the last available.

.. _Export_3DOptions_min_distance:

-  ``min_distance`` :index:`: <pair: output - export_3d - options; min_distance>` [:ref:`number <number>`] (default: ``-1``) The minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm).
   The units for this option are controlled by the `units` option.

.. _Export_3DOptions_net_filter:

-  ``net_filter`` :index:`: <pair: output - export_3d - options; net_filter>` [:ref:`string <string>`] (default: ``''``) Only include copper items belonging to nets matching this wildcard.

.. _Export_3DOptions_no_board_body:

-  ``no_board_body`` :index:`: <pair: output - export_3d - options; no_board_body>` [:ref:`boolean <boolean>`] (default: ``false``) Exclude board body.

.. _Export_3DOptions_no_components:

-  ``no_components`` :index:`: <pair: output - export_3d - options; no_components>` [:ref:`boolean <boolean>`] (default: ``false``) Exclude 3D models for components.

.. _Export_3DOptions_no_optimize_step:

-  ``no_optimize_step`` :index:`: <pair: output - export_3d - options; no_optimize_step>` [:ref:`boolean <boolean>`] (default: ``false``) Do not optimize STEP file (enables writing parametric curves).

.. _Export_3DOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - export_3d - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Export_3DOptions_subst_models:

-  ``subst_models`` :index:`: <pair: output - export_3d - options; subst_models>` [:ref:`boolean <boolean>`] (default: ``true``) Substitute STEP or IGS models with the same name in place of VRML models.

.. _Export_3DOptions_units:

-  ``units`` :index:`: <pair: output - export_3d - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches", "mils") Units used for the custom origin and `min_distance`. Affected by global options.

.. _Export_3DOptions_variant:

-  ``variant`` :index:`: <pair: output - export_3d - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

