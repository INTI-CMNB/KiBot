.. _PagesOptions:

:orphan:


PagesOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~

-  **layers** :index:`: <pair: output - pcb_print - options - pages; layers>`  [:ref:`LayerOptions parameters <LayerOptions>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'all'``) (choices: "all", "selected", "copper", "technical", "user", "inners", "outers") (also accepts any string).
-  **scaling** :index:`: <pair: output - pcb_print - options - pages; scaling>` [:ref:`number <number>`] (default: ``1.0``) Scale factor (0 means autoscaling). When not defined we use the default value for the output.
-  **sort_layers** :index:`: <pair: output - pcb_print - options - pages; sort_layers>` [:ref:`boolean <boolean>`] (default: ``false``) Try to sort the layers in the same order that uses KiCad for printing.
-  ``autoscale_margin_x`` :index:`: <pair: output - pcb_print - options - pages; autoscale_margin_x>` [:ref:`number <number>`] (default: ``0``) Horizontal margin used for the autoscaling mode [mm].
   When not defined we use the default value for the output.
-  ``autoscale_margin_y`` :index:`: <pair: output - pcb_print - options - pages; autoscale_margin_y>` [:ref:`number <number>`] (default: ``0``) Vertical margin used for the autoscaling mode [mm].
   When not defined we use the default value for the output.
-  ``colored_holes`` :index:`: <pair: output - pcb_print - options - pages; colored_holes>` [:ref:`boolean <boolean>`] (default: ``true``) Change the drill holes to be colored instead of white.
-  ``exclude_pads_from_silkscreen`` :index:`: <pair: output - pcb_print - options - pages; exclude_pads_from_silkscreen>` [:ref:`boolean <boolean>`] (default: ``false``) Do not plot the component pads in the silk screen (KiCad 5.x only).
-  ``holes_color`` :index:`: <pair: output - pcb_print - options - pages; holes_color>` [:ref:`string <string>`] (default: ``'#000000'``) Color used for the holes when `colored_holes` is enabled.
-  ``layer_var`` :index:`: <pair: output - pcb_print - options - pages; layer_var>` [:ref:`string <string>`] (default: ``'%ll'``) Text to use for the `LAYER` in the title block.
   All the expansions available for `sheet` are also available here.
-  ``line_width`` :index:`: <pair: output - pcb_print - options - pages; line_width>` [:ref:`number <number>`] (default: ``0.1``) (range: 0.02 to 2) For objects without width [mm] (KiCad 5).
-  ``mirror`` :index:`: <pair: output - pcb_print - options - pages; mirror>` [:ref:`boolean <boolean>`] (default: ``false``) Print mirrored (X axis inverted).
-  ``mirror_footprint_text`` :index:`: <pair: output - pcb_print - options - pages; mirror_footprint_text>` [:ref:`boolean <boolean>`] (default: ``true``) Mirror text in the footprints when mirror option is enabled and we plot a user layer.
-  ``mirror_pcb_text`` :index:`: <pair: output - pcb_print - options - pages; mirror_pcb_text>` [:ref:`boolean <boolean>`] (default: ``true``) Mirror text in the PCB when mirror option is enabled and we plot a user layer.
-  ``monochrome`` :index:`: <pair: output - pcb_print - options - pages; monochrome>` [:ref:`boolean <boolean>`] (default: ``false``) Print in gray scale.
-  ``negative_plot`` :index:`: <pair: output - pcb_print - options - pages; negative_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Invert black and white. Only useful for a single layer.
-  ``page_id`` :index:`: <pair: output - pcb_print - options - pages; page_id>` [:ref:`string <string>`] (default: ``'%02d'``) Text to differentiate the pages. Use %d (like in C) to get the page number.
-  ``repeat_for_layer`` :index:`: <pair: output - pcb_print - options - pages; repeat_for_layer>` [:ref:`string <string>`] (default: ``''``) Use this page as a pattern to create more pages.
   The other pages will change the layer mentioned here. |br|
   This can be used to generate a page for each copper layer, here you put `F.Cu`. |br|
   See `repeat_layers`.
-  ``repeat_inherit`` :index:`: <pair: output - pcb_print - options - pages; repeat_inherit>` [:ref:`boolean <boolean>`] (default: ``true``) If we will inherit the options of the layer we are replacing.
   Disable it if you specify the options in `repeat_layers`, which is unlikely.
-  ``repeat_layers`` :index:`: <pair: output - pcb_print - options - pages; repeat_layers>`  [:ref:`LayerOptions parameters <LayerOptions>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'inners'``) (choices: "all", "selected", "copper", "technical", "user", "inners", "outers") (also accepts any string) List
   of layers to replace `repeat_for_layer`. |br|
   This can be used to generate a page for each copper layer, here you put `copper`. |br|
   You can also use it to generate pages with drill maps, in this case use `drill_pairs` here. |br|
   Note that in this case the `repeat_for_layer` should be some drawing layer, which might contain
   a group used to insert the drill table (like in the `include_table` preflight). |br|
   Note that the drill table needs an output that generates one or more CSV files and the group in the
   PCB must be named `kibot_table_OUTPUT_FOR_CSV_DRILLS`. See the `print_drill_table.kibot.yaml` example
   in the repo. |br|
   The drill map needs KiCad 7 or newer.
-  ``sheet`` :index:`: <pair: output - pcb_print - options - pages; sheet>` [:ref:`string <string>`] (default: ``'Assembly'``) Text to use for the `SHEET` in the title block.
   Pattern (%*) and text variables are expanded. |br|
   The %ll is the list of layers included in this page. |br|
   In addition when you use `repeat_for_layer` the following patterns are available:
   %ln layer name, %ls layer suffix and %ld layer description. |br|
   When `repeat_layers` is `drill_pairs`, the following additional patterns are available:
   %lpn layer name pair, %lp layer pair. |br|
   
.. note::
   The variable name is `SHEETNAME`. Usually used as `SHEET: ${SHEETNAME}`.
..

-  ``sheet_reference_color`` :index:`: <pair: output - pcb_print - options - pages; sheet_reference_color>` [:ref:`string <string>`] (default: ``''``) Color to use for the frame and title block.
-  ``sketch_pad_line_width`` :index:`: <pair: output - pcb_print - options - pages; sketch_pad_line_width>` [:ref:`number <number>`] (default: ``0.1``) Line width for the sketched pads [mm], see `sketch_pads_on_fab_layers` (KiCad 6+)
   Note that this value is currently ignored by KiCad (6.0.9).
-  ``sketch_pads_on_fab_layers`` :index:`: <pair: output - pcb_print - options - pages; sketch_pads_on_fab_layers>` [:ref:`boolean <boolean>`] (default: ``false``) Draw the outline of the pads on the \\*.Fab layers (KiCad 6+).
-  ``tent_vias`` :index:`: <pair: output - pcb_print - options - pages; tent_vias>` [:ref:`boolean <boolean>`] (default: ``true``) Cover the vias. This option applies to KiCad 8 and older versions.
   On KiCad 9 each via can control it individually.
-  ``title`` :index:`: <pair: output - pcb_print - options - pages; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.

Used dicts
----------

- :ref:`LayerOptions parameters <LayerOptions>`
