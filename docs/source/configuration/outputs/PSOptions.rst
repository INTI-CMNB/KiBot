.. _PSOptions:

:orphan:


PSOptions parameters
~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: output - ps - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Output file name, the default KiCad name if empty.

.. note::
      KiCad will always create the file using its own name and then we can rename it. |br|
                   For this reason you must avoid generating two variants at the same directory when one of
                   them uses the default KiCad name. Affected by global options. |br|
..

-  **plot_sheet_reference** :index:`: <pair: output - ps - options; plot_sheet_reference>` [:ref:`boolean <boolean>`] (default: ``false``) Include the frame and title block. Only available for KiCad 6+ and you get a poor result
   (i.e. always the default worksheet style, also problems expanding text variables). |br|
   The `pcb_print` output can do a better job for PDF, SVG, PS, EPS and PNG outputs.
-  **scaling** :index:`: <pair: output - ps - options; scaling>` [:ref:`number <number>`] (default: ``1``) Scale factor (0 means autoscaling).
-  ``a4_output`` :index:`: <pair: output - ps - options; a4_output>` [:ref:`boolean <boolean>`] (default: ``true``) Force A4 paper size.
-  ``custom_reports`` :index:`: <pair: output - ps - options; custom_reports>`  [:ref:`CustomReport parameters <CustomReport>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) A list of customized reports for the manufacturer.
-  ``dnf_filter`` :index:`: <pair: output - ps - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``drill_marks`` :index:`: <pair: output - ps - options; drill_marks>` [:ref:`string <string>`] (default: ``'full'``) (choices: "none", "small", "full") What to use to indicate the drill places, can be none, small or full (for real scale).
-  ``edge_cut_extension`` :index:`: <pair: output - ps - options; edge_cut_extension>` [:ref:`string <string>`] (default: ``''``) Used to configure the edge cuts layer extension for Protel mode. Include the dot.
-  ``exclude_edge_layer`` :index:`: <pair: output - ps - options; exclude_edge_layer>` [:ref:`boolean <boolean>`] (default: ``true``) Do not include the PCB edge layer.
-  ``exclude_filter`` :index:`: <pair: output - ps - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_pads_from_silkscreen`` :index:`: <pair: output - ps - options; exclude_pads_from_silkscreen>` [:ref:`boolean <boolean>`] (default: ``false``) Do not plot the component pads in the silk screen (KiCad 5.x only).
-  ``force_plot_invisible_refs_vals`` :index:`: <pair: output - ps - options; force_plot_invisible_refs_vals>` [:ref:`boolean <boolean>`] (default: ``false``) Include references and values even when they are marked as invisible.
   Not available on KiCad 9.0.1 and newer.
-  ``individual_page_scaling`` :index:`: <pair: output - ps - options; individual_page_scaling>` [:ref:`boolean <boolean>`] (default: ``true``) Tell KiCad to apply the scaling for each layer as a separated entity.
   Disabling it the pages are coherent and can be superposed.
-  ``inner_extension_pattern`` :index:`: <pair: output - ps - options; inner_extension_pattern>` [:ref:`string <string>`] (default: ``''``) Used to change the Protel style extensions for inner layers.
   The replacement pattern can contain %n for the inner layer number and %N for the layer number. |br|
   Example '.g%n'. |br|

.. note::
      this numbering is consistent and the first inner layer is %n = 1 and %N = 2. Which
                   isn't true for KiCad. KiCad 8 uses 2 for the first inner and KiCad 9 uses 1. |br|
..

-  ``line_width`` :index:`: <pair: output - ps - options; line_width>` [:ref:`number <number>`] (default: ``0.15``) (range: 0.02 to 2) For objects without width [mm] (KiCad 5).
-  ``mirror_plot`` :index:`: <pair: output - ps - options; mirror_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Plot mirrored.
-  ``negative_plot`` :index:`: <pair: output - ps - options; negative_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Invert black and white.
-  ``plot_footprint_refs`` :index:`: <pair: output - ps - options; plot_footprint_refs>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint references.
-  ``plot_footprint_values`` :index:`: <pair: output - ps - options; plot_footprint_values>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint values.
-  ``pre_transform`` :index:`: <pair: output - ps - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``scale_adjust_x`` :index:`: <pair: output - ps - options; scale_adjust_x>` [:ref:`number <number>`] (default: ``1.0``) Fine grain adjust for the X scale (floating point multiplier).
-  ``scale_adjust_y`` :index:`: <pair: output - ps - options; scale_adjust_y>` [:ref:`number <number>`] (default: ``1.0``) Fine grain adjust for the Y scale (floating point multiplier).
-  ``sketch_pad_line_width`` :index:`: <pair: output - ps - options; sketch_pad_line_width>` [:ref:`number <number>`] (default: ``0.1``) Line width for the sketched pads [mm], see `sketch_pads_on_fab_layers` (KiCad 6+)
   Note that this value is currently ignored by KiCad (6.0.9).
-  ``sketch_pads_on_fab_layers`` :index:`: <pair: output - ps - options; sketch_pads_on_fab_layers>` [:ref:`boolean <boolean>`] (default: ``false``) Draw only the outline of the pads on the \\*.Fab layers (KiCad 6+).
-  ``sketch_plot`` :index:`: <pair: output - ps - options; sketch_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Don't fill objects, just draw the outline.
-  ``tent_vias`` :index:`: <pair: output - ps - options; tent_vias>` [:ref:`boolean <boolean>`] (default: ``true``) Cover the vias. Usable for KiCad versions older than 9.
   
.. warning::
   KiCad 8 has a bug that ignores this option. Set it from KiCad GUI.
..

-  ``uppercase_extensions`` :index:`: <pair: output - ps - options; uppercase_extensions>` [:ref:`boolean <boolean>`] (default: ``false``) Use uppercase names for the extensions.
-  ``variant`` :index:`: <pair: output - ps - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
-  ``width_adjust`` :index:`: <pair: output - ps - options; width_adjust>` [:ref:`number <number>`] (default: ``0``) This width factor is intended to compensate PS printers/plotters that do not strictly obey line width settings.
   Only used to plot pads and tracks.

Used dicts
----------

- :ref:`CustomReport parameters <CustomReport>`
