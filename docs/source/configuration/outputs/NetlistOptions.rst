.. _NetlistOptions:

:orphan:


NetlistOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~


.. _NetlistOptions_format:

-  **format** :index:`: <pair: output - netlist - options; format>` [:ref:`string <string>`] (default: ``'classic'``) (choices: "classic", "ipc", "orcadpcb2", "allegro", "pads", "cadstar", "spice", "spicemodel", "kicadxml") The `classic` format is the KiCad
   internal format, and is generated from the schematic. |br|
   The `ipc` format is the IPC-D-356 format, useful for PCB testing, is generated from the PCB. |br|
   kicadxml, cadstar, orcadpcb2, spice and spicemodel needs KiCad 8 or newer. |br|
   allegro and pads needs KiCad 9 or newer.

.. _NetlistOptions_output:

-  **output** :index:`: <pair: output - netlist - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output

   - classic: (%i=netlist, %x=net)
   - ipc: (%i=IPC-D-356, %x=d356)
   - orcadpcb2: (%i=orcad, %x=net)
   - allegro: (%i=allegro, %x=txt)
   - pads: (%i=pads, %x=asc)
   - cadstar: (%i=cadstar, %x=frp)
   - spice: (%i=spice, %x=cir)
   - spicemodel: (%i=model, %x=cir)
   - kicadxml: (%i=netlist, %x=xml). Affected by global options.

.. _NetlistOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - netlist - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _NetlistOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - netlist - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _NetlistOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - netlist - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _NetlistOptions_variant:

-  ``variant`` :index:`: <pair: output - netlist - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Used for sub-PCBs.

