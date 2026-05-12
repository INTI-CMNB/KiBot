.. _BoardViewOptions:

:orphan:


BoardViewOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: output - boardview - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=boardview, %x=brd/brv). Affected by global options.
-  ``dnf_filter`` :index:`: <pair: output - boardview - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - boardview - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``format`` :index:`: <pair: output - boardview - options; format>` [:ref:`string <string>`] (default: ``'BRD'``) (choices: "BRD", "BVR", "OBDATA") Format used for the generated file. The BVR file format is bigger but keeps
   more information, like alphanumeric pin names. |br|
   OBDATA is the OpenBoardData format. You can include the manufacturer part number defining the global
   `field_part_number` variable. Excluded and not fitted components are marked with `-` status.
-  ``pre_transform`` :index:`: <pair: output - boardview - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``sorted`` :index:`: <pair: output - boardview - options; sorted>` [:ref:`boolean <boolean>`] (default: ``true``) Sort components by reference. Disable this option to get a file closer to what
   kicad-boardview generates.
-  ``variant`` :index:`: <pair: output - boardview - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Used for sub-PCBs.

