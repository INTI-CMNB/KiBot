.. _IPC2581Options:

:orphan:


IPC2581Options parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: output - ipc2581 - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=IPC-2581, %x=zip/xml)
   The extension depends on the compress option. Affected by global options.
-  ``compress`` :index:`: <pair: output - ipc2581 - options; compress>` [:ref:`boolean <boolean>`] (default: ``true``) Compress the XML file as a *zip* file.
-  ``dnf_filter`` :index:`: <pair: output - ipc2581 - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - ipc2581 - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``field_dist_part_number`` :index:`: <pair: output - ipc2581 - options; field_dist_part_number>` [:ref:`string <string>`] (default: ``'_field_dist_part_number'``) Name of the field used for the distributor part number.
   Use the `field_dist_part_number` global variable to define `_field_dist_part_number`.
-  ``field_distributor`` :index:`: <pair: output - ipc2581 - options; field_distributor>` [:ref:`string <string>`] (default: ``'_field_distributor'``) Name of the field used for the distributor.
   Use the `field_distributor` global variable to define `_field_distributor`.
-  ``field_internal_id`` :index:`: <pair: output - ipc2581 - options; field_internal_id>` [:ref:`string <string>`] (default: ``''``) Name of the field used as an internal ID.
   Leave empty to create unique IDs.
-  ``field_manufacturer`` :index:`: <pair: output - ipc2581 - options; field_manufacturer>` [:ref:`string <string>`] (default: ``'_field_manufacturer'``) Name of the field used for the manufacturer.
   Use the `field_manufacturer` global variable to define `_field_manufacturer`.
-  ``field_part_number`` :index:`: <pair: output - ipc2581 - options; field_part_number>` [:ref:`string <string>`] (default: ``'_field_part_number'``) Name of the field used for the manufacturer part number.
   Use the `field_part_number` global variable to define `_field_part_number`.
-  ``pre_transform`` :index:`: <pair: output - ipc2581 - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``precision`` :index:`: <pair: output - ipc2581 - options; precision>` [:ref:`number <number>`] (default: ``6``) Number of decimals used to represent the values.
-  ``units`` :index:`: <pair: output - ipc2581 - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches") Units used for the positions. Affected by global options.
   Note that when using *mils* as global units this option becomes *inches*.
-  ``variant`` :index:`: <pair: output - ipc2581 - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
-  ``version`` :index:`: <pair: output - ipc2581 - options; version>` [:ref:`string <string>`] (default: ``'C'``) (choices: "B", "C") Which implementation of the IPC-2581 standard will be generated.

