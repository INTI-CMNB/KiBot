.. _ODBOptions:

:orphan:


ODBOptions parameters
~~~~~~~~~~~~~~~~~~~~~

-  **compression** :index:`: <pair: output - odb - options; compression>` [:ref:`string <string>`] (default: ``'zip'``) (choices: "zip", "tgz", "none") For *zip* files the structure is at the root.
   *tgz* is gzip compressed tarball, usually smaller than a *zip* file. |br|
   In this case data is inside a directory named *odb*, not the root. |br|
   When using *none* you get a directory containing all the data.
-  **output** :index:`: <pair: output - odb - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=odb, %x=zip/tgz/none)
   The extension depends on the compression option. |br|
   Note that for `none` we get a directory, not a file. Affected by global options.
-  ``dnf_filter`` :index:`: <pair: output - odb - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - odb - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``pre_transform`` :index:`: <pair: output - odb - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``precision`` :index:`: <pair: output - odb - options; precision>` [:ref:`number <number>`] (default: ``6``) Number of decimals used to represent the values.
-  ``units`` :index:`: <pair: output - odb - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches") Units used for the positions. Affected by global options.
   Note that when using *mils* as global units this option becomes *inches*.
-  ``variant`` :index:`: <pair: output - odb - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

