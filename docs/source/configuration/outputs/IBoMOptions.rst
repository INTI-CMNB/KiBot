.. _IBoMOptions:

:orphan:


IBoMOptions parameters
~~~~~~~~~~~~~~~~~~~~~~

-  **board_rotation** :index:`: <pair: output - ibom - options; board_rotation>` [:ref:`number <number>`] (default: ``0``) Board rotation in degrees (-180 to 180). Will be rounded to multiple of 5.
-  **bom_view** :index:`: <pair: output - ibom - options; bom_view>` [:ref:`string <string>`] (default: ``'left-right'``) (choices: "bom-only", "left-right", "top-bottom") Default BOM view.
-  **extra_fields** :index:`: <pair: output - ibom - options; extra_fields>` [:ref:`string <string>`] (default: ``''``) Comma separated list of extra fields to pull from netlist or xml file.
   Using 'X,Y' is a shortcut for `show_fields` and `group_fields` with values 'Value,Footprint,X,Y'.
-  **include_tracks** :index:`: <pair: output - ibom - options; include_tracks>` [:ref:`boolean <boolean>`] (default: ``false``) Include track/zone information in output. F.Cu and B.Cu layers only.
-  **layer_view** :index:`: <pair: output - ibom - options; layer_view>` [:ref:`string <string>`] (default: ``'FB'``) (choices: "F", "FB", "B") Default layer view.
-  **normalize_field_case** :index:`: <pair: output - ibom - options; normalize_field_case>` [:ref:`boolean <boolean>`] (default: ``false``) Normalize extra field name case. E.g. 'MPN' and 'mpn' will be considered the same field.
-  **output** :index:`: <pair: output - ibom - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output, use '' to use the IBoM filename (%i=ibom, %x=html). Affected by global options.
-  **show_fields** :index:`: <pair: output - ibom - options; show_fields>` [:ref:`string <string>`] (default: ``''``) Comma separated list of fields to show in the BOM.
   Value and Footprint are displayed when nothing is specified.
-  ``blacklist`` :index:`: <pair: output - ibom - options; blacklist>` [:ref:`string <string>`] (default: ``''``) List of comma separated blacklisted components or prefixes with *. E.g. 'X1,MH*'.
   IBoM option, avoid using in conjunction with KiBot variants/filters.
-  ``blacklist_empty_val`` :index:`: <pair: output - ibom - options; blacklist_empty_val>` [:ref:`boolean <boolean>`] (default: ``false``) Blacklist components with empty value.
   IBoM option, avoid using in conjunction with KiBot variants/filters.
-  ``checkboxes`` :index:`: <pair: output - ibom - options; checkboxes>` [:ref:`string <string>`] (default: ``'Sourced,Placed'``) Comma separated list of checkbox columns.
-  ``dark_mode`` :index:`: <pair: output - ibom - options; dark_mode>` [:ref:`boolean <boolean>`] (default: ``false``) Default to dark mode.
-  ``dnf_filter`` :index:`: <pair: output - ibom - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant. |br|
   Avoid using it in conjunction with IBoM native filtering options.

-  ``dnp_field`` :index:`: <pair: output - ibom - options; dnp_field>` [:ref:`string <string>`] (default: ``''``) Name of the extra field that indicates do not populate status.
   Components with this field not empty will be blacklisted. |br|
   IBoM option, avoid using in conjunction with KiBot variants/filters.
-  ``exclude_filter`` :index:`: <pair: output - ibom - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``extra_data_file`` :index:`: <pair: output - ibom - options; extra_data_file>` [:ref:`string <string>`] (default: ``''``) Path to netlist or xml file. You can use '%F.xml' to avoid specifying the project name.
   Leave it blank for most uses, data will be extracted from the PCB.
-  ``forced_name`` :index:`: <pair: output - ibom - options; forced_name>` [:ref:`string <string>`] (default: ``''``) Name to be used for the PCB/project (no file extension).
   This will affect the name iBoM displays in the generated HTML.
-  ``group_fields`` :index:`: <pair: output - ibom - options; group_fields>` [:ref:`string <string>`] (default: ``''``) Comma separated list of fields that components will be grouped by.
   Value and Footprint are used when nothing is specified.
-  ``hide_excluded`` :index:`: <pair: output - ibom - options; hide_excluded>` [:ref:`boolean <boolean>`] (default: ``false``) Hide components in the Fab layer that are marked as excluded by a variant.
   Affected by global options.
-  ``hide_pads`` :index:`: <pair: output - ibom - options; hide_pads>` [:ref:`boolean <boolean>`] (default: ``false``) Hide footprint pads by default.
-  ``hide_silkscreen`` :index:`: <pair: output - ibom - options; hide_silkscreen>` [:ref:`boolean <boolean>`] (default: ``false``) Hide silkscreen by default.
-  ``highlight_pin1`` :index:`: <pair: output - ibom - options; highlight_pin1>` [:ref:`boolean <boolean>` | :ref:`string <string>`] (default: ``false``) (choices: "none", "all", "selected") Highlight pin1 by default.
-  ``include_nets`` :index:`: <pair: output - ibom - options; include_nets>` [:ref:`boolean <boolean>`] (default: ``false``) Include netlist information in output..
-  ``mark_when_checked`` :index:`: <pair: output - ibom - options; mark_when_checked>` [:ref:`string <string>`] (default: ``''``) Name of the checkbox column used to mark components when checked.
   When enabled components checked in this column will be displayed in green. |br|
   Leave empty to disable it. |br|
   Needs iBoM newer than 2.10.0. |br|.
-  ``name_format`` :index:`: <pair: output - ibom - options; name_format>` [:ref:`string <string>`] (default: ``'ibom'``) Output file name format supports substitutions:
   %f : original pcb file name without extension. |br|
   %p : pcb/project title from pcb metadata. |br|
   %c : company from pcb metadata. |br|
   %r : revision from pcb metadata. |br|
   %d : pcb date from metadata if available, file modification date otherwise. |br|
   %D : bom generation date. |br|
   %T : bom generation time. |br|
   Extension .html will be added automatically. |br|
   Note that this name is used only when output is ''.
-  *netlist_file* :index:`: <pair: output - ibom - options; netlist_file>` Alias for extra_data_file.
-  ``no_blacklist_virtual`` :index:`: <pair: output - ibom - options; no_blacklist_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Do not blacklist virtual components.
   IBoM option, avoid using in conjunction with KiBot variants/filters.
-  ``no_compression`` :index:`: <pair: output - ibom - options; no_compression>` [:ref:`boolean <boolean>`] (default: ``false``) Disable compression of pcb data.
-  ``no_redraw_on_drag`` :index:`: <pair: output - ibom - options; no_redraw_on_drag>` [:ref:`boolean <boolean>`] (default: ``false``) Do not redraw pcb on drag by default.
-  ``offset_back_rotation`` :index:`: <pair: output - ibom - options; offset_back_rotation>` [:ref:`boolean <boolean>`] (default: ``false``) Offset the back of the pcb by 180 degrees.
-  ``pre_transform`` :index:`: <pair: output - ibom - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``show_fabrication`` :index:`: <pair: output - ibom - options; show_fabrication>` [:ref:`boolean <boolean>`] (default: ``false``) Show fabrication layer by default.
-  ``sort_order`` :index:`: <pair: output - ibom - options; sort_order>` [:ref:`string <string>`] (default: ``'C,R,L,D,U,Y,X,F,SW,A,~,HS,CNN,J,P,NT,MH'``) Default sort order for components. Must contain '~' once.
-  ``variant`` :index:`: <pair: output - ibom - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Avoid using it in conjunction with IBoM native filtering options.
-  ``variant_field`` :index:`: <pair: output - ibom - options; variant_field>` [:ref:`string <string>`] (default: ``''``) Name of the extra field that stores board variant for component.
   IBoM option, avoid using in conjunction with KiBot variants/filters.
-  ``variants_blacklist`` :index:`: <pair: output - ibom - options; variants_blacklist>` [:ref:`string <string>`] (default: ``''``) List of board variants to exclude from the BOM.
   IBoM option, avoid using in conjunction with KiBot variants/filters.
-  ``variants_whitelist`` :index:`: <pair: output - ibom - options; variants_whitelist>` [:ref:`string <string>`] (default: ``''``) List of board variants to include in the BOM.
   IBoM option, avoid using in conjunction with KiBot variants/filters.

