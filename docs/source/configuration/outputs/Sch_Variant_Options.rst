.. _Sch_Variant_Options:


Sch_Variant_Options parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``copy_project`` :index:`: <pair: output - sch_variant - options; copy_project>` [:ref:`boolean <boolean>`] (default: ``false``) Copy the KiCad project to the destination directory.
   Disabled by default for compatibility with older versions.
-  ``dnf_filter`` :index:`: <pair: output - sch_variant - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - sch_variant - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``pre_transform`` :index:`: <pair: output - sch_variant - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``title`` :index:`: <pair: output - sch_variant - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.
-  ``variant`` :index:`: <pair: output - sch_variant - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

