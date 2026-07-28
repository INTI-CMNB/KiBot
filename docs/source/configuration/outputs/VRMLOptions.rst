.. _VRMLOptions:

:orphan:


VRMLOptions parameters
~~~~~~~~~~~~~~~~~~~~~~


.. _VRMLOptions_download:

-  **download** :index:`: <pair: output - vrml - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.

.. _VRMLOptions_no_virtual:

-  **no_virtual** :index:`: <pair: output - vrml - options; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.

.. _VRMLOptions_output:

-  **output** :index:`: <pair: output - vrml - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=vrml, %x=wrl). Affected by global options.

.. _VRMLOptions_show_components:

-  **show_components** :index:`: <pair: output - vrml - options; show_components>` [:ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'all'``) (choices: "none", "all") (also accepts any string) List of components to draw, can be also a string for `none` or `all`.
   Ranges like *R5-R10* are supported. |br|
   Unlike the `pcbdraw` output, the default is `all`.


.. _VRMLOptions_dir_models:

-  ``dir_models`` :index:`: <pair: output - vrml - options; dir_models>` [:ref:`string <string>`] (default: ``'shapes3D'``) Subdirectory used to store the 3D models for the components.
   If you want to create a monolithic file just use '' here. |br|
   Note that the WRL file will contain relative paths to the models.

.. _VRMLOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - vrml - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _VRMLOptions_download_lcsc:

-  ``download_lcsc`` :index:`: <pair: output - vrml - options; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.

.. _VRMLOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - vrml - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _VRMLOptions_highlight:

-  ``highlight`` :index:`: <pair: output - vrml - options; highlight>` [:ref:`list(string) <list(string)>`] (default: ``[]``) List of components to highlight. Ranges like *R5-R10* are supported.


.. _VRMLOptions_highlight_on_top:

-  ``highlight_on_top`` :index:`: <pair: output - vrml - options; highlight_on_top>` [:ref:`boolean <boolean>`] (default: ``false``) Highlight over the component (not under).

.. _VRMLOptions_highlight_padding:

-  ``highlight_padding`` :index:`: <pair: output - vrml - options; highlight_padding>` [:ref:`number <number>`] (default: ``1.5``) (range: 0 to 1000) How much the highlight extends around the component [mm].

.. _VRMLOptions_kicad_3d_url:

-  ``kicad_3d_url`` :index:`: <pair: output - vrml - options; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/api/v4/projects/21604637/repository/files/'``) Base URL for the KiCad 3D models.

.. _VRMLOptions_kicad_3d_url_suffix:

-  ``kicad_3d_url_suffix`` :index:`: <pair: output - vrml - options; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``'/raw?ref=VERSION'``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.

.. _VRMLOptions_kicad_3d_url_version:

-  ``kicad_3d_url_version`` :index:`: <pair: output - vrml - options; kicad_3d_url_version>` [:ref:`boolean <boolean>`] (default: ``true``) Replace the *master* subdir in the URL by the KiCad version.
   In this way we download the 3D model corresponding to the installed KiCad instead
   of the last available.

.. _VRMLOptions_model_units:

-  ``model_units`` :index:`: <pair: output - vrml - options; model_units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "meters", "deciinches", "inches") Units used for the VRML (1 deciinch = 0.1 inches).

.. _VRMLOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - vrml - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _VRMLOptions_ref_units:

-  ``ref_units`` :index:`: <pair: output - vrml - options; ref_units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches'") Units for `ref_x` and `ref_y`.

.. _VRMLOptions_ref_x:

-  ``ref_x`` :index:`: <pair: output - vrml - options; ref_x>` [:ref:`number <number>`] (default: ``0``) X coordinate to use as reference when `use_pcb_center_as_ref` and `use_pcb_center_as_ref` are disabled.

.. _VRMLOptions_ref_y:

-  ``ref_y`` :index:`: <pair: output - vrml - options; ref_y>` [:ref:`number <number>`] (default: ``0``) Y coordinate to use as reference when `use_pcb_center_as_ref` and `use_pcb_center_as_ref` are disabled.

.. _VRMLOptions_use_aux_axis_as_origin:

-  ``use_aux_axis_as_origin`` :index:`: <pair: output - vrml - options; use_aux_axis_as_origin>` [:ref:`boolean <boolean>`] (default: ``false``) Use the auxiliary axis as origin for coordinates.
   Has more precedence than `use_pcb_center_as_ref`.

.. _VRMLOptions_use_pcb_center_as_ref:

-  ``use_pcb_center_as_ref`` :index:`: <pair: output - vrml - options; use_pcb_center_as_ref>` [:ref:`boolean <boolean>`] (default: ``true``) The center of the PCB will be used as reference point.
   When disabled the `ref_x`, `ref_y` and `ref_units` will be used.

.. _VRMLOptions_variant:

-  ``variant`` :index:`: <pair: output - vrml - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

