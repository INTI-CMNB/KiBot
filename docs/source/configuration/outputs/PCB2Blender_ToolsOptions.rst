.. _PCB2Blender_ToolsOptions:


PCB2Blender_ToolsOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: output - pcb2blender_tools - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=pcb2blender, %x=pcb3d). Affected by global options.
-  **show_components** :index:`: <pair: output - pcb2blender_tools - options; show_components>` [:ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'all'``) (choices: "none", "all") (also accepts any string) List of components to include in the pads list,
   can be also a string for `none` or `all`. Ranges like *R5-R10* are supported.

-  ``board_bounds_create`` :index:`: <pair: output - pcb2blender_tools - options; board_bounds_create>` [:ref:`boolean <boolean>`] (default: ``true``) Create the file that informs the size of the used PCB area.
   This is the bounding box reported by KiCad for the PCB edge with 1 mm of margin.
-  ``board_bounds_dir`` :index:`: <pair: output - pcb2blender_tools - options; board_bounds_dir>` [:ref:`string <string>`] (default: ``'layers'``) Sub-directory where the bounds file is stored.
-  ``board_bounds_file`` :index:`: <pair: output - pcb2blender_tools - options; board_bounds_file>` [:ref:`string <string>`] (default: ``'bounds'``) Name of the bounds file.
-  ``board_bounds_format`` :index:`: <pair: output - pcb2blender_tools - options; board_bounds_format>` [:ref:`string <string>`] (default: ``'BIN'``) (choices: "BIN", "TOML") Format for the board bounds file, also sub-boards. Use 'TOML' for 2.17+.
-  ``dnf_filter`` :index:`: <pair: output - pcb2blender_tools - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - pcb2blender_tools - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``pads_info_create`` :index:`: <pair: output - pcb2blender_tools - options; pads_info_create>` [:ref:`boolean <boolean>`] (default: ``true``) Create the files containing the PCB pads information.
-  ``pads_info_dir`` :index:`: <pair: output - pcb2blender_tools - options; pads_info_dir>` [:ref:`string <string>`] (default: ``'pads'``) Sub-directory where the pads info files are stored.
-  ``pads_info_format`` :index:`: <pair: output - pcb2blender_tools - options; pads_info_format>` [:ref:`string <string>`] (default: ``'BIN'``) (choices: "BIN", "TOML") Format for the pads. Use 'TOML' for 2.17+.
-  ``pre_transform`` :index:`: <pair: output - pcb2blender_tools - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``solder_join_on_heatsink`` :index:`: <pair: output - pcb2blender_tools - options; solder_join_on_heatsink>` [:ref:`boolean <boolean>`] (default: ``true``) Solder the THT pads with heatsink fabrication attribute.
-  ``stackup_create`` :index:`: <pair: output - pcb2blender_tools - options; stackup_create>` [:ref:`boolean <boolean>`] (default: ``false``) Create a file containing the board stackup.
-  ``stackup_dir`` :index:`: <pair: output - pcb2blender_tools - options; stackup_dir>` [:ref:`string <string>`] (default: ``'.'``) Directory for the stackup file. Use 'layers' for 2.7+.
-  ``stackup_file`` :index:`: <pair: output - pcb2blender_tools - options; stackup_file>` [:ref:`string <string>`] (default: ``'board.yaml'``) Name for the stackup file. Use 'stackup' for 2.7+.
-  ``stackup_format`` :index:`: <pair: output - pcb2blender_tools - options; stackup_format>` [:ref:`string <string>`] (default: ``'JSON'``) (choices: "JSON", "BIN", "TOML") Format for the stackup file. Use 'BIN' for 2.7+.
-  ``sub_boards_bounds_file`` :index:`: <pair: output - pcb2blender_tools - options; sub_boards_bounds_file>` [:ref:`string <string>`] (default: ``'bounds'``) File name for the sub-PCBs bounds.
-  ``sub_boards_create`` :index:`: <pair: output - pcb2blender_tools - options; sub_boards_create>` [:ref:`boolean <boolean>`] (default: ``true``) Extract sub-PCBs and their Z axis position.
-  ``sub_boards_dir`` :index:`: <pair: output - pcb2blender_tools - options; sub_boards_dir>` [:ref:`string <string>`] (default: ``'boards'``) Directory for the boards definitions.
-  ``sub_boards_stacked_prefix`` :index:`: <pair: output - pcb2blender_tools - options; sub_boards_stacked_prefix>` [:ref:`string <string>`] (default: ``'stacked\_'``) Prefix used for the stack files.
-  ``variant`` :index:`: <pair: output - pcb2blender_tools - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

