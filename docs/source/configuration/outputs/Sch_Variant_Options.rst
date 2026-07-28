.. _Sch_Variant_Options:

:orphan:


Sch_Variant_Options parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _Sch_Variant_Options_copy_project:

-  ``copy_project`` :index:`: <pair: output - sch_variant - options; copy_project>` [:ref:`boolean <boolean>`] (default: ``false``) Copy the KiCad project to the destination directory.
   Disabled by default for compatibility with older versions.

.. _Sch_Variant_Options_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - sch_variant - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Sch_Variant_Options_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - sch_variant - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Sch_Variant_Options_include:

-  ``include`` :index:`: <pair: output - sch_variant - options; include>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_all\_'``) [:ref:`comma separated <comma_sep>`] When exporting a KiCad 10 file also include the listed variants.
   The `_all_` keyword means all other variants. |br|
   The variant indicated by the `variant` option will be the `Default` KiCad variant.


.. _Sch_Variant_Options_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - sch_variant - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Sch_Variant_Options_title:

-  ``title`` :index:`: <pair: output - sch_variant - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.

.. _Sch_Variant_Options_variant:

-  ``variant`` :index:`: <pair: output - sch_variant - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

