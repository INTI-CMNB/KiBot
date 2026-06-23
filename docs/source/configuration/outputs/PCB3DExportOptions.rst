.. _PCB3DExportOptions:

:orphan:


PCB3DExportOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _PCB3DExportOptions_download:

-  **download** :index:`: <pair: output - blender_export - options - pcb3d; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.

.. _PCB3DExportOptions_no_virtual:

-  **no_virtual** :index:`: <pair: output - blender_export - options - pcb3d; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.

.. _PCB3DExportOptions_show_components:

-  **show_components** :index:`: <pair: output - blender_export - options - pcb3d; show_components>` [:ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'all'``) (choices: "none", "all") (also accepts any string) List of components to draw, can be also a string for `none` or `all`.
   Ranges like *R5-R10* are supported. |br|
   Unlike the `pcbdraw` output, the default is `all`.


.. _PCB3DExportOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - blender_export - options - pcb3d; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PCB3DExportOptions_download_lcsc:

-  ``download_lcsc`` :index:`: <pair: output - blender_export - options - pcb3d; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.

.. _PCB3DExportOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - blender_export - options - pcb3d; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PCB3DExportOptions_highlight:

-  ``highlight`` :index:`: <pair: output - blender_export - options - pcb3d; highlight>` [:ref:`list(string) <list(string)>`] (default: ``[]``) List of components to highlight. Ranges like *R5-R10* are supported.


.. _PCB3DExportOptions_highlight_on_top:

-  ``highlight_on_top`` :index:`: <pair: output - blender_export - options - pcb3d; highlight_on_top>` [:ref:`boolean <boolean>`] (default: ``false``) Highlight over the component (not under).

.. _PCB3DExportOptions_highlight_padding:

-  ``highlight_padding`` :index:`: <pair: output - blender_export - options - pcb3d; highlight_padding>` [:ref:`number <number>`] (default: ``1.5``) (range: 0 to 1000) How much the highlight extends around the component [mm].

.. _PCB3DExportOptions_kicad_3d_url:

-  ``kicad_3d_url`` :index:`: <pair: output - blender_export - options - pcb3d; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/api/v4/projects/21604637/repository/files/'``) Base URL for the KiCad 3D models.

.. _PCB3DExportOptions_kicad_3d_url_suffix:

-  ``kicad_3d_url_suffix`` :index:`: <pair: output - blender_export - options - pcb3d; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``'/raw?ref=VERSION'``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.

.. _PCB3DExportOptions_kicad_3d_url_version:

-  ``kicad_3d_url_version`` :index:`: <pair: output - blender_export - options - pcb3d; kicad_3d_url_version>` [:ref:`boolean <boolean>`] (default: ``true``) Replace the *master* subdir in the URL by the KiCad version.
   In this way we download the 3D model corresponding to the installed KiCad instead
   of the last available.

.. _PCB3DExportOptions_output:

-  ``output`` :index:`: <pair: output - blender_export - options - pcb3d; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated PCB3D file (%i='blender_export' %x='pcb3d'). Affected by global options.

.. _PCB3DExportOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - blender_export - options - pcb3d; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PCB3DExportOptions_solder_join_on_heatsink:

-  ``solder_join_on_heatsink`` :index:`: <pair: output - blender_export - options - pcb3d; solder_join_on_heatsink>` [:ref:`boolean <boolean>`] (default: ``true``) Solder the THT pads with heatsink fabrication attribute.

.. _PCB3DExportOptions_solder_paste_for_populated:

-  ``solder_paste_for_populated`` :index:`: <pair: output - blender_export - options - pcb3d; solder_paste_for_populated>` [:ref:`boolean <boolean>`] (default: ``true``) Add solder paste only for the populated components.
   Populated components are the ones listed in `show_components`.

.. _PCB3DExportOptions_variant:

-  ``variant`` :index:`: <pair: output - blender_export - options - pcb3d; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

.. _PCB3DExportOptions_version:

-  ``version`` :index:`: <pair: output - blender_export - options - pcb3d; version>` [:ref:`string <string>`] (default: ``'2.7'``) (choices: "2.1", "2.1_haschtl", "2.7") Variant of the format used.

