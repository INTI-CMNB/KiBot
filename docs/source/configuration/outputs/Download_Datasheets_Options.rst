.. _Download_Datasheets_Options:

:orphan:


Download_Datasheets_Options parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **field** :index:`: <pair: output - download_datasheets - options; field>` [:ref:`string <string>`] (default: ``'Datasheet'``) Name of the field containing the URL.
-  ``classify`` :index:`: <pair: output - download_datasheets - options; classify>` [:ref:`boolean <boolean>`] (default: ``false``) Use the reference to classify the components in different sub-dirs.
   In this way C7 will go into a Capacitors sub-dir, R3 into Resistors, etc.
-  ``classify_extra`` :index:`: <pair: output - download_datasheets - options; classify_extra>` [:ref:`string_dict <string_dict>`] (default: empty dict, default values used) Extra reference associations used to classify the references.
   They are pairs `Reference prefix` -> `Sub-dir`.

-  ``dnf`` :index:`: <pair: output - download_datasheets - options; dnf>` [:ref:`boolean <boolean>`] (default: ``false``) Include the DNF components.
-  ``dnf_filter`` :index:`: <pair: output - download_datasheets - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - download_datasheets - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``link_repeated`` :index:`: <pair: output - download_datasheets - options; link_repeated>` [:ref:`boolean <boolean>`] (default: ``true``) Instead of download things we already downloaded use symlinks.
-  ``output`` :index:`: <pair: output - download_datasheets - options; output>` [:ref:`string <string>`] (default: ``'${VALUE}.pdf'``) Name used for the downloaded datasheet.
   `${FIELD}` will be replaced by the FIELD content.
-  ``pre_transform`` :index:`: <pair: output - download_datasheets - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``repeated`` :index:`: <pair: output - download_datasheets - options; repeated>` [:ref:`boolean <boolean>`] (default: ``false``) Download URLs that we already downloaded.
   It only makes sense if the `output` field makes their output different.
-  ``variant`` :index:`: <pair: output - download_datasheets - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

