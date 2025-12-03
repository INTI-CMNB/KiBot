.. _STEPOptions:

:orphan:


STEPOptions parameters
~~~~~~~~~~~~~~~~~~~~~~

-  **download** :index:`: <pair: output - step - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.
-  **no_virtual** :index:`: <pair: output - step - options; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.
-  **origin** :index:`: <pair: output - step - options; origin>` [:ref:`string <string>`] (default: ``'grid'``) (choices: "grid", "drill") (also accepts any string) Determines the coordinates origin. Using grid the coordinates are the same as you have in the
   design sheet. |br|
   The drill option uses the auxiliary reference defined by the user. |br|
   You can define any other origin using the format 'X,Y', i.e. '3.2,-10'.
-  **output** :index:`: <pair: output - step - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated STEP file (%i='3D' %x='step'). Affected by global options.
-  ``dnf_filter`` :index:`: <pair: output - step - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``download_lcsc`` :index:`: <pair: output - step - options; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.
-  ``exclude_filter`` :index:`: <pair: output - step - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``kicad_3d_url`` :index:`: <pair: output - step - options; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'``) Base URL for the KiCad 3D models.
-  ``kicad_3d_url_suffix`` :index:`: <pair: output - step - options; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``''``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.
-  ``metric_units`` :index:`: <pair: output - step - options; metric_units>` [:ref:`boolean <boolean>`] (default: ``true``) Use metric units instead of inches.
-  ``min_distance`` :index:`: <pair: output - step - options; min_distance>` [:ref:`number <number>`] (default: ``-1``) The minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm).
-  ``pre_transform`` :index:`: <pair: output - step - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``subst_models`` :index:`: <pair: output - step - options; subst_models>` [:ref:`boolean <boolean>`] (default: ``true``) Substitute STEP or IGS models with the same name in place of VRML models.
-  ``variant`` :index:`: <pair: output - step - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

