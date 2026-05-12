.. _GenCADOptions:

:orphan:


GenCADOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: output - gencad - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=gencad, %x=cad). Affected by global options.
-  ``aux_origin`` :index:`: <pair: output - gencad - options; aux_origin>` [:ref:`boolean <boolean>`] (default: ``false``) Use auxiliary axis as origin.
-  ``dnf_filter`` :index:`: <pair: output - gencad - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - gencad - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``flip_bottom_padstacks`` :index:`: <pair: output - gencad - options; flip_bottom_padstacks>` [:ref:`boolean <boolean>`] (default: ``false``) Flip bottom footprint padstacks.
-  ``no_reuse_shapes`` :index:`: <pair: output - gencad - options; no_reuse_shapes>` [:ref:`boolean <boolean>`] (default: ``false``) Generate a new shape for each footprint instance (Do not reuse shapes).
-  ``pre_transform`` :index:`: <pair: output - gencad - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``save_origin`` :index:`: <pair: output - gencad - options; save_origin>` [:ref:`boolean <boolean>`] (default: ``false``) Save the origin coordinates in the file.
-  ``unique_pin_names`` :index:`: <pair: output - gencad - options; unique_pin_names>` [:ref:`boolean <boolean>`] (default: ``false``) Generate unique pin names.
-  ``variant`` :index:`: <pair: output - gencad - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Used for sub-PCBs.

