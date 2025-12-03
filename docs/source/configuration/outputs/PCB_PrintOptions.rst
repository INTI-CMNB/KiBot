.. _PCB_PrintOptions:

:orphan:


PCB_PrintOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **color_theme** :index:`: <pair: output - pcb_print - options; color_theme>` [:ref:`string <string>`] (default: ``'_builtin_classic'``) Selects the color theme. Only applies to KiCad 6.
   To use the KiCad 6 default colors select `_builtin_default`. |br|
   Usually user colors are stored as `user`, but you can give it another name.
-  **force_edge_cuts** :index:`: <pair: output - pcb_print - options; force_edge_cuts>` [:ref:`boolean <boolean>`] (default: ``false``) Add the `Edge.Cuts` to all the pages.
-  **format** :index:`: <pair: output - pcb_print - options; format>` [:ref:`string <string>`] (default: ``'PDF'``) (choices: "PDF", "SVG", "PNG", "EPS", "PS") Format for the output file/s.
   Note that for PS you need `ghostscript` which isn't part of the default docker images.
-  **output** :index:`: <pair: output - pcb_print - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=assembly, %x=pdf/ps)/(%i=assembly_page_NN, %x=svg/png/eps).
   Consult the `page_number_as_extension` and `page_id` options. Affected by global options.
-  *output_name* :index:`: <pair: output - pcb_print - options; output_name>` Alias for output.
-  **pages** :index:`: <pair: output - pcb_print - options; pages>`  [:ref:`PagesOptions parameters <PagesOptions>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) List of pages to include in the output document.
   Each page contains one or more layers of the PCB.
-  **plot_sheet_reference** :index:`: <pair: output - pcb_print - options; plot_sheet_reference>` [:ref:`boolean <boolean>`] (default: ``true``) Include the title-block (worksheet, frame, etc.).
-  **scaling** :index:`: <pair: output - pcb_print - options; scaling>` [:ref:`number <number>`] (default: ``1.0``) Default scale factor (0 means autoscaling).
-  ``add_background`` :index:`: <pair: output - pcb_print - options; add_background>` [:ref:`boolean <boolean>`] (default: ``false``) Add a background to the pages, see `background_color`.
-  ``autoscale_margin_x`` :index:`: <pair: output - pcb_print - options; autoscale_margin_x>` [:ref:`number <number>`] (default: ``0``) Default horizontal margin used for the autoscaling mode [mm].
-  ``autoscale_margin_y`` :index:`: <pair: output - pcb_print - options; autoscale_margin_y>` [:ref:`number <number>`] (default: ``0``) Default vertical margin used for the autoscaling mode [mm].
-  ``background_color`` :index:`: <pair: output - pcb_print - options; background_color>` [:ref:`string <string>`] (default: ``'#FFFFFF'``) Color for the background when `add_background` is enabled.
-  ``background_image`` :index:`: <pair: output - pcb_print - options; background_image>` [:ref:`string <string>`] (default: ``''``) Background image, must be an SVG, only when `add_background` is enabled.
-  ``blind_via_color`` :index:`: <pair: output - pcb_print - options; blind_via_color>` [:ref:`string <string>`] (default: ``''``) Color used for blind/buried `colored_vias`.
-  ``colored_pads`` :index:`: <pair: output - pcb_print - options; colored_pads>` [:ref:`boolean <boolean>`] (default: ``true``) Plot through-hole in a different color. Like KiCad GUI does.
-  ``colored_vias`` :index:`: <pair: output - pcb_print - options; colored_vias>` [:ref:`boolean <boolean>`] (default: ``true``) Plot vias in a different color. Like KiCad GUI does.
-  ``dnf_filter`` :index:`: <pair: output - pcb_print - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``dpi`` :index:`: <pair: output - pcb_print - options; dpi>` [:ref:`number <number>`] (default: ``360``) (range: 36 to 1200) Resolution (Dots Per Inch) for the output file. Most objects are vectors, but thing
   like the the solder mask are handled as images by the conversion tools.
-  ``drill`` :index:`: <pair: output - pcb_print - options; drill>`  [:ref:`DrillOptions parameters <DrillOptions>`] [:ref:`boolean <boolean>` | :ref:`dict <dict>`] (default: ``false``) Use a boolean for simple cases or fine-tune its behavior.
   Used to customize the `drill_pairs` option to print drill maps.
-  ``drill_marks`` :index:`: <pair: output - pcb_print - options; drill_marks>` [:ref:`string <string>`] (default: ``'full'``) (choices: "none", "small", "full") What to use to indicate the drill places, can be none, small or full (for real scale).
-  ``exclude_filter`` :index:`: <pair: output - pcb_print - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``forced_edge_cuts_color`` :index:`: <pair: output - pcb_print - options; forced_edge_cuts_color>` [:ref:`string <string>`] (default: ``''``) Color used for the `force_edge_cuts` option.
-  ``forced_edge_cuts_use_for_center`` :index:`: <pair: output - pcb_print - options; forced_edge_cuts_use_for_center>` [:ref:`boolean <boolean>`] (default: ``true``) Used when enabling the `force_edge_cuts`, in this case this is the `use_for_center` option of the forced
   layer.
-  ``frame_plot_mechanism`` :index:`: <pair: output - pcb_print - options; frame_plot_mechanism>` [:ref:`string <string>`] (default: ``'internal'``) (choices: "gui", "internal", "plot") Plotting the frame from Python is problematic.
   This option selects a workaround strategy. |br|
   gui: uses KiCad GUI to do it. Is slow but you get the correct frame. |br|
   But it can't keep track of page numbers. |br|
   internal: KiBot loads the `.kicad_wks` and does the drawing work. |br|
   Best option, but some details are different from what the GUI generates. |br|
   plot: uses KiCad Python API. Not available for KiCad 5. |br|
   You get the default frame and some substitutions doesn't work.
-  ``hide_excluded`` :index:`: <pair: output - pcb_print - options; hide_excluded>` [:ref:`boolean <boolean>`] (default: ``false``) Hide components in the Fab layer that are marked as excluded by a variant.
   Affected by global options.
-  ``include_table`` :index:`: <pair: output - pcb_print - options; include_table>`  [:ref:`IncludeTableOptions parameters <IncludeTableOptions>`] [:ref:`boolean <boolean>` | :ref:`dict <dict>`] (default: ``false``) Use a boolean for simple cases or fine-tune its behavior.
   When enabled we include tables using the same mechanism used in the `include_table`
   preflight. The result isn't saved to disk.
-  ``individual_page_scaling`` :index:`: <pair: output - pcb_print - options; individual_page_scaling>` [:ref:`boolean <boolean>`] (default: ``true``) Tell KiCad to apply the scaling for each page as a separated entity.
   Disabling it the pages are coherent and can be superposed.
-  ``invert_use_for_center`` :index:`: <pair: output - pcb_print - options; invert_use_for_center>` [:ref:`boolean <boolean>`] (default: ``false``) Invert the meaning of the `use_for_center` layer option.
   This can be used to just select the edge cuts for centering, in this case enable this option
   and disable the `use_for_center` option of the edge cuts layer.
-  ``keep_temporal_files`` :index:`: <pair: output - pcb_print - options; keep_temporal_files>` [:ref:`boolean <boolean>`] (default: ``false``) Store the temporal page and layer files in the output dir and don't delete them.
-  ``micro_via_color`` :index:`: <pair: output - pcb_print - options; micro_via_color>` [:ref:`string <string>`] (default: ``''``) Color used for micro `colored_vias`.
-  ``pad_color`` :index:`: <pair: output - pcb_print - options; pad_color>` [:ref:`string <string>`] (default: ``''``) Color used for `colored_pads`.
-  ``page_number_as_extension`` :index:`: <pair: output - pcb_print - options; page_number_as_extension>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled the %i is always `assembly`, the %x will be NN.FORMAT (i.e. 01.png).
   Note: page numbers can be customized using the `page_id` option for each page.
-  ``png_width`` :index:`: <pair: output - pcb_print - options; png_width>` [:ref:`number <number>`] (default: ``1280``) (range: 0 to 7680) Width of the PNG in pixels. Use 0 to use as many pixels as the DPI needs for the page size.
-  ``pre_transform`` :index:`: <pair: output - pcb_print - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``realistic_solder_mask`` :index:`: <pair: output - pcb_print - options; realistic_solder_mask>` [:ref:`boolean <boolean>`] (default: ``true``) Try to draw the solder mask as a real solder mask, not the negative used for fabrication.
   In order to get a good looking select a color with transparency, i.e. '#14332440'. |br|
   PcbDraw must be installed in order to use this option.
-  ``sheet_reference_layout`` :index:`: <pair: output - pcb_print - options; sheet_reference_layout>` [:ref:`string <string>`] (default: ``''``) Worksheet file (.kicad_wks) to use. Leave empty to use the one specified in the project.
   
.. warning::
   you must provide a project.
..

-  ``svg_precision`` :index:`: <pair: output - pcb_print - options; svg_precision>` [:ref:`number <number>`] (default: ``4``) (range: 0 to 6) Scale factor used to represent 1 mm in the SVG (KiCad 6).
   The value is how much zeros has the multiplier (1 mm = 10 power `svg_precision` units). |br|
   Note that for an A4 paper Firefox 91 and Chrome 105 can't handle more than 5.
-  ``title`` :index:`: <pair: output - pcb_print - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.
-  ``variant`` :index:`: <pair: output - pcb_print - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
-  ``via_color`` :index:`: <pair: output - pcb_print - options; via_color>` [:ref:`string <string>`] (default: ``''``) Color used for through-hole `colored_vias`.

Used dicts
----------

- :ref:`DrillOptions parameters <DrillOptions>`
- :ref:`IncludeTableOptions parameters <IncludeTableOptions>`
- :ref:`PagesOptions parameters <PagesOptions>`
