.. _DrawFancyStackupOptions_pre:

:orphan:


DrawFancyStackupOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **columns** :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; columns>`  [:ref:`SUColumnsFancy parameters <SUColumnsFancy_pre>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>`] (default: computed for your project) List of columns to display.
   Can be just the name of the column. |br|
   Available columns are *drawing*, *material*, *layer*, *thickness*, *dielectric*, *layer_type*, *gerber*. |br|
   When empty KiBot will add them in the above order, skipping the *gerber* if not available.
-  **draw_stackup** :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; draw_stackup>` [:ref:`boolean <boolean>`] (default: ``true``) Choose whether to display the stackup drawing or not.
-  **gerber** :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; gerber>` [:ref:`string <string>`] (default: ``''``) Name of the output used to generate the gerbers. This is needed only when you
   want to include the *gerber* column, containing the gerber file names.
-  **gerber_extension_only** :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; gerber_extension_only>` [:ref:`boolean <boolean>`] (default: ``true``) Only display the gerber file extension instead of full gerber name.
-  ``border_thickness`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; border_thickness>` [:ref:`number <number>`] (default: ``0.15``) Thickness of the borders of stackup drawing and stackup table.
-  ``column_spacing`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; column_spacing>` [:ref:`number <number>`] (default: ``2``) Blank space (in number of characters) between columns in the stackup table.
-  ``core_extra_spacing_ratio`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; core_extra_spacing_ratio>` [:ref:`number <number>`] (default: ``2``) Extra vertical space given to the core layers.
-  ``draw_vias`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; draw_vias>` [:ref:`boolean <boolean>`] (default: ``true``) Enable drawing vias (thru, blind, buried) in the stackup table.
-  ``drawing_border_spacing`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; drawing_border_spacing>` [:ref:`number <number>`] (default: ``10``) Space (in number of characters) between stackup drawing borders and via drawings.
-  ``enabled`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; enabled>` [:ref:`boolean <boolean>`] (default: ``true``) Enable the check. This is the replacement for the boolean value.
-  ``group_name`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; group_name>` [:ref:`string <string>`] (default: ``'kibot_fancy_stackup'``) Name for the group containing the drawings. If KiBot can't find it will create
   a new group at the specified coordinates for the indicated layer.
-  ``layer`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; layer>` [:ref:`string <string>`] (default: ``'Cmts.User'``) Layer used for the stackup. Only used when the group can't be found.
   Otherwise we use the layer for the first object in the group.
-  ``layer_spacing`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; layer_spacing>` [:ref:`number <number>`] (default: ``3``) Space (in number of characters) between layers on the stackup table/drawing.
-  ``note`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; note>` [:ref:`string <string>`] (default: ``''``) Note to write at the bottom of the stackup table. Leave empty if no note is to be written.
-  ``pos_x`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; pos_x>` [:ref:`number <number>`] (default: ``19``) X position in the PCB. The units are defined by the global *units* variable.
   Only used when the group can't be found.
-  ``pos_y`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; pos_y>` [:ref:`number <number>`] (default: ``100``) Y position in the PCB. The units are defined by the global *units* variable.
   Only used when the group can't be found.
-  ``stackup_to_text_lines_spacing`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; stackup_to_text_lines_spacing>` [:ref:`number <number>`] (default: ``3``) Space (in number of characters) between stackup drawing and stackup table.
-  ``via_spacing`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; via_spacing>` [:ref:`number <number>`] (default: ``8``) Space (in number of characters) between vias in the stackup drawing.
-  ``via_width`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; via_width>` [:ref:`number <number>`] (default: ``4``) Width (in number of characters) of a via in the stackup drawing.
-  ``width`` :index:`: <pair: preflight - draw_fancy_stackup - draw_fancy_stackup; width>` [:ref:`number <number>`] (default: ``120``) Width for the drawing. The units are defined by the global *units* variable.
   Only used when the group can't be found.

Used dicts
----------

- :ref:`SUColumnsFancy parameters <SUColumnsFancy_pre>`
