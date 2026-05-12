.. _PCB_StatsOptions:

:orphan:


PCB_StatsOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **format** :index:`: <pair: output - pcb_stats - options; format>` [:ref:`string <string>`] (default: ``'txt'``) (choices: "txt", "json") Output file format.
-  **output** :index:`: <pair: output - pcb_stats - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated report file (%i='statistics' %x='txt/json'). Affected by global options.
-  ``dnf_filter`` :index:`: <pair: output - pcb_stats - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - pcb_stats - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_footprints_without_pads`` :index:`: <pair: output - pcb_stats - options; exclude_footprints_without_pads>` [:ref:`boolean <boolean>`] (default: ``false``) Exclude footprints without pads.
-  ``pre_transform`` :index:`: <pair: output - pcb_stats - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``subtract_holes_from_board`` :index:`: <pair: output - pcb_stats - options; subtract_holes_from_board>` [:ref:`boolean <boolean>`] (default: ``false``) Subtract holes from the board area.
-  ``subtract_holes_from_copper`` :index:`: <pair: output - pcb_stats - options; subtract_holes_from_copper>` [:ref:`boolean <boolean>`] (default: ``false``) Subtract holes from copper areas.
-  ``units`` :index:`: <pair: output - pcb_stats - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches") Units used for the values. Affected by global options.
-  ``variant`` :index:`: <pair: output - pcb_stats - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

