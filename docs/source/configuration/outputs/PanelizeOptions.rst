.. _PanelizeOptions:

:orphan:


PanelizeOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **configs** :index:`: <pair: output - panelize - options; configs>`  [:ref:`PanelizeConfig parameters <PanelizeConfig>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``[]``) One or more configurations used to create the panel.
   Use a string to include an external configuration, i.e. `myDefault.json`. |br|
   You can also include a preset using `:name`, i.e. `:vcuts`. |br|
   Use a dict to specify the options using the KiBot YAML file.
-  **output** :index:`: <pair: output - panelize - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=panel, %x=kicad_pcb). Affected by global options.
-  ``copy_lib_tables`` :index:`: <pair: output - panelize - options; copy_lib_tables>` [:ref:`boolean <boolean>`] (default: ``false``) If the target directory is different than the one containing the PCB copy the symbol and
   footprint lib tables.
-  ``copy_vias_on_mask`` :index:`: <pair: output - panelize - options; copy_vias_on_mask>` [:ref:`string <string>`] (default: ``'auto'``) (choices: "auto", "yes", "no") Copy the GUI option to plot vias on the mask layers from the original PCB to
   the panel. |br|
   This option is a workaround to KiCad 8 not allowing to choose to plot (or not to plot) vias
   on the mask layers using the Python API. So you have to set it in the GUI, but this option
   is lost during panelization. |br|
   Setting this option to *auto* will copy the value for faulty KiCad 8 versions, but won't
   waste time for working KiCad versions.
-  ``create_preview`` :index:`: <pair: output - panelize - options; create_preview>` [:ref:`boolean <boolean>`] (default: ``false``) Use PcbDraw to create a preview of the panel.
-  ``default_angles`` :index:`: <pair: output - panelize - options; default_angles>` [:ref:`string <string>`] (default: ``'deg'``) (choices: "deg", "°", "rad") Angles used when omitted.
-  ``dnf_filter`` :index:`: <pair: output - panelize - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - panelize - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``pre_transform`` :index:`: <pair: output - panelize - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``title`` :index:`: <pair: output - panelize - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.
-  ``units`` :index:`: <pair: output - panelize - options; units>` [:ref:`string <string>`] (default: ``'mm'``) (choices: "millimeters", "inches", "mils", "mm", "cm", "dm", "m", "mil", "inch", "in") Units used when omitted.
-  ``variant`` :index:`: <pair: output - panelize - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

Used dicts
----------

- :ref:`PanelizeConfig parameters <PanelizeConfig>`
