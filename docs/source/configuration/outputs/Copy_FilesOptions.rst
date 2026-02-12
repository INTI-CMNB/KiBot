.. _Copy_FilesOptions:

:orphan:


Copy_FilesOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **download** :index:`: <pair: output - copy_files - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Downloads missing 3D models from KiCad git.
   Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR. |br|
   They are downloaded to a temporal directory and discarded. |br|
   If you want to cache the downloaded files specify a directory using the
   KIBOT_3D_MODELS environment variable.
-  **files** :index:`: <pair: output - copy_files - options; files>`  [:ref:`FilesListCopy parameters <FilesListCopy>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Which files will be included.
-  **no_virtual** :index:`: <pair: output - copy_files - options; no_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Used to exclude 3D models for components with 'virtual' attribute.
-  ``dnf_filter`` :index:`: <pair: output - copy_files - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``download_lcsc`` :index:`: <pair: output - copy_files - options; download_lcsc>` [:ref:`boolean <boolean>`] (default: ``true``) In addition to try to download the 3D models from KiCad git also try to get
   them from LCSC database. In order to work you'll need to provide the LCSC
   part number. The field containing the LCSC part number is defined by the
   `field_lcsc_part` global variable.
-  ``exclude_filter`` :index:`: <pair: output - copy_files - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``expand_dest`` :index:`: <pair: output - copy_files - options; expand_dest>` [:ref:`boolean <boolean>`] (default: ``true``) Also expand the `dest` file name (using % patterns).
-  ``follow_links`` :index:`: <pair: output - copy_files - options; follow_links>` [:ref:`boolean <boolean>`] (default: ``true``) Store the file pointed by symlinks, not the symlink.
-  ``kicad_3d_url`` :index:`: <pair: output - copy_files - options; kicad_3d_url>` [:ref:`string <string>`] (default: ``'https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'``) Base URL for the KiCad 3D models.
-  ``kicad_3d_url_suffix`` :index:`: <pair: output - copy_files - options; kicad_3d_url_suffix>` [:ref:`string <string>`] (default: ``''``) Text added to the end of the download URL.
   Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2.
-  ``kicad_3d_url_version`` :index:`: <pair: output - copy_files - options; kicad_3d_url_version>` [:ref:`boolean <boolean>`] (default: ``true``) Replace the *master* subdir in the URL by the KiCad version.
   In this way we download the 3D model corresponding to the installed KiCad instead
   of the last available.
-  ``link_no_copy`` :index:`: <pair: output - copy_files - options; link_no_copy>` [:ref:`boolean <boolean>`] (default: ``false``) Create symlinks instead of copying files.
-  ``pre_transform`` :index:`: <pair: output - copy_files - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``variant`` :index:`: <pair: output - copy_files - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

Used dicts
----------

- :ref:`FilesListCopy parameters <FilesListCopy>`
