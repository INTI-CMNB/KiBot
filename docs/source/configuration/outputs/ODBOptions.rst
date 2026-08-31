.. _ODBOptions:

:orphan:


ODBOptions parameters
~~~~~~~~~~~~~~~~~~~~~


.. _ODBOptions_compression:

-  **compression** :index:`: <pair: output - odb - options; compression>` [:ref:`string <string>`] (default: ``'zip'``) (choices: "zip", "tgz", "none") For *zip* files the structure is at the root.
   *tgz* is gzip compressed tarball, usually smaller than a *zip* file. |br|
   In this case data is inside a directory named *odb*, not the root. |br|
   When using *none* you get a directory containing all the data.

.. _ODBOptions_output:

-  **output** :index:`: <pair: output - odb - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=odb, %x=zip/tgz/none)
   The extension depends on the compression option. |br|
   Note that for `none` we get a directory, not a file. Affected by global options.

.. _ODBOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - odb - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _ODBOptions_drawing_sheet:

-  ``drawing_sheet`` :index:`: <pair: output - odb - options; drawing_sheet>` [:ref:`string <string>`] (default: ``''``) Path to drawing sheet, this overrides any existing project defined sheet when used.

.. _ODBOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - odb - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _ODBOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - odb - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _ODBOptions_precision:

-  ``precision`` :index:`: <pair: output - odb - options; precision>` [:ref:`number <number>`] (default: ``6``) Number of decimals used to represent the values.

.. _ODBOptions_units:

-  ``units`` :index:`: <pair: output - odb - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches") Units used for the positions. Affected by global options.
   Note that when using *mils* as global units this option becomes *inches*.

.. _ODBOptions_variant:

-  ``variant`` :index:`: <pair: output - odb - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

