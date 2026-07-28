.. _PCB2Blender_ToolsOptions:

:orphan:


PCB2Blender_ToolsOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _PCB2Blender_ToolsOptions_output:

-  **output** :index:`: <pair: output - pcb2blender_tools - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=pcb2blender, %x=pcb3d). Affected by global options.

.. _PCB2Blender_ToolsOptions_show_components:

-  **show_components** :index:`: <pair: output - pcb2blender_tools - options; show_components>` [:ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'all'``) (choices: "none", "all") (also accepts any string) List of components to include in the pads list,
   can be also a string for `none` or `all`. Ranges like *R5-R10* are supported.


.. _PCB2Blender_ToolsOptions_board_bounds_create:

-  ``board_bounds_create`` :index:`: <pair: output - pcb2blender_tools - options; board_bounds_create>` [:ref:`boolean <boolean>`] (default: ``true``) Create the file that informs the size of the used PCB area.
   This is the bounding box reported by KiCad for the PCB edge with 1 mm of margin.

.. _PCB2Blender_ToolsOptions_board_bounds_dir:

-  ``board_bounds_dir`` :index:`: <pair: output - pcb2blender_tools - options; board_bounds_dir>` [:ref:`string <string>`] (default: ``'layers'``) Sub-directory where the bounds file is stored.

.. _PCB2Blender_ToolsOptions_board_bounds_file:

-  ``board_bounds_file`` :index:`: <pair: output - pcb2blender_tools - options; board_bounds_file>` [:ref:`string <string>`] (default: ``'bounds'``) Name of the bounds file.

.. _PCB2Blender_ToolsOptions_board_bounds_format:

-  ``board_bounds_format`` :index:`: <pair: output - pcb2blender_tools - options; board_bounds_format>` [:ref:`string <string>`] (default: ``'BIN'``) (choices: "BIN", "TOML") Format for the board bounds file, also sub-boards. Use 'TOML' for 2.17+.

.. _PCB2Blender_ToolsOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - pcb2blender_tools - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PCB2Blender_ToolsOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - pcb2blender_tools - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PCB2Blender_ToolsOptions_pads_info_create:

-  ``pads_info_create`` :index:`: <pair: output - pcb2blender_tools - options; pads_info_create>` [:ref:`boolean <boolean>`] (default: ``true``) Create the files containing the PCB pads information.

.. _PCB2Blender_ToolsOptions_pads_info_dir:

-  ``pads_info_dir`` :index:`: <pair: output - pcb2blender_tools - options; pads_info_dir>` [:ref:`string <string>`] (default: ``'pads'``) Sub-directory where the pads info files are stored.

.. _PCB2Blender_ToolsOptions_pads_info_format:

-  ``pads_info_format`` :index:`: <pair: output - pcb2blender_tools - options; pads_info_format>` [:ref:`string <string>`] (default: ``'BIN'``) (choices: "BIN", "TOML") Format for the pads. Use 'TOML' for 2.17+.

.. _PCB2Blender_ToolsOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - pcb2blender_tools - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PCB2Blender_ToolsOptions_solder_join_on_heatsink:

-  ``solder_join_on_heatsink`` :index:`: <pair: output - pcb2blender_tools - options; solder_join_on_heatsink>` [:ref:`boolean <boolean>`] (default: ``true``) Solder the THT pads with heatsink fabrication attribute.

.. _PCB2Blender_ToolsOptions_stackup_create:

-  ``stackup_create`` :index:`: <pair: output - pcb2blender_tools - options; stackup_create>` [:ref:`boolean <boolean>`] (default: ``false``) Create a file containing the board stackup.

.. _PCB2Blender_ToolsOptions_stackup_dir:

-  ``stackup_dir`` :index:`: <pair: output - pcb2blender_tools - options; stackup_dir>` [:ref:`string <string>`] (default: ``'.'``) Directory for the stackup file. Use 'layers' for 2.7+.

.. _PCB2Blender_ToolsOptions_stackup_file:

-  ``stackup_file`` :index:`: <pair: output - pcb2blender_tools - options; stackup_file>` [:ref:`string <string>`] (default: ``'board.yaml'``) Name for the stackup file. Use 'stackup' for 2.7+.

.. _PCB2Blender_ToolsOptions_stackup_format:

-  ``stackup_format`` :index:`: <pair: output - pcb2blender_tools - options; stackup_format>` [:ref:`string <string>`] (default: ``'JSON'``) (choices: "JSON", "BIN", "TOML") Format for the stackup file. Use 'BIN' for 2.7+.

.. _PCB2Blender_ToolsOptions_sub_boards_bounds_file:

-  ``sub_boards_bounds_file`` :index:`: <pair: output - pcb2blender_tools - options; sub_boards_bounds_file>` [:ref:`string <string>`] (default: ``'bounds'``) File name for the sub-PCBs bounds.

.. _PCB2Blender_ToolsOptions_sub_boards_create:

-  ``sub_boards_create`` :index:`: <pair: output - pcb2blender_tools - options; sub_boards_create>` [:ref:`boolean <boolean>`] (default: ``true``) Extract sub-PCBs and their Z axis position.

.. _PCB2Blender_ToolsOptions_sub_boards_dir:

-  ``sub_boards_dir`` :index:`: <pair: output - pcb2blender_tools - options; sub_boards_dir>` [:ref:`string <string>`] (default: ``'boards'``) Directory for the boards definitions.

.. _PCB2Blender_ToolsOptions_sub_boards_stacked_prefix:

-  ``sub_boards_stacked_prefix`` :index:`: <pair: output - pcb2blender_tools - options; sub_boards_stacked_prefix>` [:ref:`string <string>`] (default: ``'stacked\_'``) Prefix used for the stack files.

.. _PCB2Blender_ToolsOptions_variant:

-  ``variant`` :index:`: <pair: output - pcb2blender_tools - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

