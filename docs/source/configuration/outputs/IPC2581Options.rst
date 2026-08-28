.. _IPC2581Options:

:orphan:


IPC2581Options parameters
~~~~~~~~~~~~~~~~~~~~~~~~~


.. _IPC2581Options_output:

-  **output** :index:`: <pair: output - ipc2581 - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=IPC-2581, %x=zip/xml)
   The extension depends on the compress option. Affected by global options.

.. _IPC2581Options_bom_revision:

-  ``bom_revision`` :index:`: <pair: output - ipc2581 - options; bom_revision>` [:ref:`string <string>`] (default: ``''``) BOM revision to use in the output file. Defaults to schematic revision from the project file.
   Needs KiCad 10+.

.. _IPC2581Options_compress:

-  ``compress`` :index:`: <pair: output - ipc2581 - options; compress>` [:ref:`boolean <boolean>`] (default: ``true``) Compress the XML file as a *zip* file.

.. _IPC2581Options_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - ipc2581 - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _IPC2581Options_drawing_sheet:

-  ``drawing_sheet`` :index:`: <pair: output - ipc2581 - options; drawing_sheet>` [:ref:`string <string>`] (default: ``''``) Path to drawing sheet, this overrides any existing project defined sheet when used.

.. _IPC2581Options_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - ipc2581 - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _IPC2581Options_field_dist_part_number:

-  ``field_dist_part_number`` :index:`: <pair: output - ipc2581 - options; field_dist_part_number>` [:ref:`string <string>`] (default: ``'_field_dist_part_number'``) Name of the field used for the distributor part number.
   Use the `field_dist_part_number` global variable to define `_field_dist_part_number`.

.. _IPC2581Options_field_distributor:

-  ``field_distributor`` :index:`: <pair: output - ipc2581 - options; field_distributor>` [:ref:`string <string>`] (default: ``'_field_distributor'``) Name of the field used for the distributor.
   Use the `field_distributor` global variable to define `_field_distributor`.

.. _IPC2581Options_field_internal_id:

-  ``field_internal_id`` :index:`: <pair: output - ipc2581 - options; field_internal_id>` [:ref:`string <string>`] (default: ``''``) Name of the field used as an internal ID.
   Leave empty to create unique IDs.

.. _IPC2581Options_field_manufacturer:

-  ``field_manufacturer`` :index:`: <pair: output - ipc2581 - options; field_manufacturer>` [:ref:`string <string>`] (default: ``'_field_manufacturer'``) Name of the field used for the manufacturer.
   Use the `field_manufacturer` global variable to define `_field_manufacturer`.

.. _IPC2581Options_field_part_number:

-  ``field_part_number`` :index:`: <pair: output - ipc2581 - options; field_part_number>` [:ref:`string <string>`] (default: ``'_field_part_number'``) Name of the field used for the manufacturer part number.
   Use the `field_part_number` global variable to define `_field_part_number`.

.. _IPC2581Options_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - ipc2581 - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _IPC2581Options_precision:

-  ``precision`` :index:`: <pair: output - ipc2581 - options; precision>` [:ref:`number <number>`] (default: ``6``) Number of decimals used to represent the values.

.. _IPC2581Options_units:

-  ``units`` :index:`: <pair: output - ipc2581 - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches") Units used for the positions. Affected by global options.
   Note that when using *mils* as global units this option becomes *inches*.

.. _IPC2581Options_variant:

-  ``variant`` :index:`: <pair: output - ipc2581 - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

.. _IPC2581Options_version:

-  ``version`` :index:`: <pair: output - ipc2581 - options; version>` [:ref:`string <string>`] (default: ``'C'``) (choices: "B", "C") Which implementation of the IPC-2581 standard will be generated.

