.. _JobSetOptions:

:orphan:


JobSetOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~

-  **download** :index:`: <pair: output - jobset - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.
-  **jobset** :index:`: <pair: output - jobset - options; jobset>` [:ref:`string <string>`] (default: ``''``) Name of the KiCad jobset file you want to use. Should have `kicad_jobset` extension.
   Leave empty to look for a jobset with the same name as the project.
-  **no_virtual** :index:`: <pair: output - jobset - options; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.
-  **run_output** :index:`: <pair: output - jobset - options; run_output>` [:ref:`string <string>`] (default: ``''``) Output to be generated. When empty KiCad runs all possible outputs.
   Here the name can be obtained from the .kicad_jobset file, in JSON format. |br|
   The `outputs` section contains all the defined outputs. Each output has an `id` use it here.
-  ``dnf_filter`` :index:`: <pair: output - jobset - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``download_lcsc`` :index:`: <pair: output - jobset - options; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.
-  ``exclude_filter`` :index:`: <pair: output - jobset - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``kicad_3d_url`` :index:`: <pair: output - jobset - options; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/api/v4/projects/21604637/repository/files/'``) Base URL for the KiCad 3D models.
-  ``kicad_3d_url_suffix`` :index:`: <pair: output - jobset - options; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``'/raw?ref=VERSION'``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.
-  ``kicad_3d_url_version`` :index:`: <pair: output - jobset - options; kicad_3d_url_version>` [:ref:`boolean <boolean>`] (default: ``true``) Replace the *master* subdir in the URL by the KiCad version.
   In this way we download the 3D model corresponding to the installed KiCad instead
   of the last available.
-  ``pre_transform`` :index:`: <pair: output - jobset - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``stop_on_error`` :index:`: <pair: output - jobset - options; stop_on_error>` [:ref:`boolean <boolean>`] (default: ``true``) Stop generation when an error is detected.
-  ``variant`` :index:`: <pair: output - jobset - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

