.. _DXFOptions:

:orphan:


DXFOptions parameters
~~~~~~~~~~~~~~~~~~~~~


.. _DXFOptions_output:

-  **output** :index:`: <pair: output - dxf - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Output file name, the default KiCad name if empty.

.. note::
   KiCad will always create the file using its own name and then we can rename it. |br|
   For this reason you must avoid generating two variants at the same directory when one of
   them uses the default KiCad name. Affected by global options. |br|
..


.. _DXFOptions_plot_sheet_reference:

-  **plot_sheet_reference** :index:`: <pair: output - dxf - options; plot_sheet_reference>` [:ref:`boolean <boolean>`] (default: ``false``) Include the frame and title block. Only available for KiCad 6+ and you get a poor result
   (i.e. always the default worksheet style, also problems expanding text variables). |br|
   The `pcb_print` output can do a better job for PDF, SVG, PS, EPS and PNG outputs.

.. _DXFOptions_scaling:

-  **scaling** :index:`: <pair: output - dxf - options; scaling>` [:ref:`number <number>`] (default: ``1``) Scale factor (0 means autoscaling).

.. _DXFOptions_custom_reports:

-  ``custom_reports`` :index:`: <pair: output - dxf - options; custom_reports>`  [:ref:`CustomReport parameters <CustomReport>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) A list of customized reports for the manufacturer.

.. _DXFOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - dxf - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _DXFOptions_drill_marks:

-  ``drill_marks`` :index:`: <pair: output - dxf - options; drill_marks>` [:ref:`string <string>`] (default: ``'full'``) (choices: "none", "small", "full") What to use to indicate the drill places, can be none, small or full (for real scale).

.. _DXFOptions_edge_cut_extension:

-  ``edge_cut_extension`` :index:`: <pair: output - dxf - options; edge_cut_extension>` [:ref:`string <string>`] (default: ``''``) Used to configure the edge cuts layer extension for Protel mode. Include the dot.

.. _DXFOptions_exclude_edge_layer:

-  ``exclude_edge_layer`` :index:`: <pair: output - dxf - options; exclude_edge_layer>` [:ref:`boolean <boolean>`] (default: ``true``) Do not include the PCB edge layer.

.. _DXFOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - dxf - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _DXFOptions_exclude_pads_from_silkscreen:

-  ``exclude_pads_from_silkscreen`` :index:`: <pair: output - dxf - options; exclude_pads_from_silkscreen>` [:ref:`boolean <boolean>`] (default: ``false``) Do not plot the component pads in the silk screen (KiCad 5.x only).

.. _DXFOptions_force_plot_invisible_refs_vals:

-  ``force_plot_invisible_refs_vals`` :index:`: <pair: output - dxf - options; force_plot_invisible_refs_vals>` [:ref:`boolean <boolean>`] (default: ``false``) Include references and values even when they are marked as invisible.
   Not available on KiCad 9.0.1 and newer.

.. _DXFOptions_individual_page_scaling:

-  ``individual_page_scaling`` :index:`: <pair: output - dxf - options; individual_page_scaling>` [:ref:`boolean <boolean>`] (default: ``true``) Tell KiCad to apply the scaling for each layer as a separated entity.
   Disabling it the pages are coherent and can be superposed.

.. _DXFOptions_inner_extension_pattern:

-  ``inner_extension_pattern`` :index:`: <pair: output - dxf - options; inner_extension_pattern>` [:ref:`string <string>`] (default: ``''``) Used to change the Protel style extensions for inner layers.
   The replacement pattern can contain %n for the inner layer number and %N for the layer number. |br|
   Example '.g%n'. |br|

.. note::
   this numbering is consistent and the first inner layer is %n = 1 and %N = 2. Which
   isn't true for KiCad. KiCad 8 uses 2 for the first inner and KiCad 9 uses 1. |br|
..


.. _DXFOptions_metric_units:

-  ``metric_units`` :index:`: <pair: output - dxf - options; metric_units>` [:ref:`boolean <boolean>`] (default: ``false``) Use mm instead of inches.

.. _DXFOptions_plot_footprint_refs:

-  ``plot_footprint_refs`` :index:`: <pair: output - dxf - options; plot_footprint_refs>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint references.

.. _DXFOptions_plot_footprint_values:

-  ``plot_footprint_values`` :index:`: <pair: output - dxf - options; plot_footprint_values>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint values.

.. _DXFOptions_polygon_mode:

-  ``polygon_mode`` :index:`: <pair: output - dxf - options; polygon_mode>` [:ref:`boolean <boolean>`] (default: ``true``) Plot using the contour, instead of the center line.
   You must disable it to get the dimensions (See https://gitlab.com/kicad/code/kicad/-/issues/11901).

.. _DXFOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - dxf - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _DXFOptions_sketch_pad_line_width:

-  ``sketch_pad_line_width`` :index:`: <pair: output - dxf - options; sketch_pad_line_width>` [:ref:`number <number>`] (default: ``0.1``) Line width for the sketched pads [mm], see :ref:`sketch_pads_on_fab_layers <DXFOptions_sketch_pads_on_fab_layers>` (KiCad 6+)
   Note that this value is currently ignored by KiCad (6.0.9).

.. _DXFOptions_sketch_pad_numbers:

-  ``sketch_pad_numbers`` :index:`: <pair: output - dxf - options; sketch_pad_numbers>` [:ref:`boolean <boolean>`] (default: ``false``) Plot pad numbers on top of sketched pads on the \\*.Fab layers (KiCad 11+).

.. _DXFOptions_sketch_pads_on_fab_layers:

-  ``sketch_pads_on_fab_layers`` :index:`: <pair: output - dxf - options; sketch_pads_on_fab_layers>` [:ref:`boolean <boolean>`] (default: ``false``) Draw only the outline of the pads on the \\*.Fab layers (KiCad 6+).

.. _DXFOptions_sketch_plot:

-  ``sketch_plot`` :index:`: <pair: output - dxf - options; sketch_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Don't fill objects, just draw the outline.

.. _DXFOptions_tent_vias:

-  ``tent_vias`` :index:`: <pair: output - dxf - options; tent_vias>` [:ref:`boolean <boolean>`] (default: ``true``) Cover the vias. Usable for KiCad versions older than 9.
   
.. warning::
   KiCad 8 has a bug that ignores this option. Set it from KiCad GUI.
..


.. _DXFOptions_uppercase_extensions:

-  ``uppercase_extensions`` :index:`: <pair: output - dxf - options; uppercase_extensions>` [:ref:`boolean <boolean>`] (default: ``false``) Use uppercase names for the extensions.

.. _DXFOptions_use_aux_axis_as_origin:

-  ``use_aux_axis_as_origin`` :index:`: <pair: output - dxf - options; use_aux_axis_as_origin>` [:ref:`boolean <boolean>`] (default: ``false``) Use the auxiliary axis as origin for coordinates.

.. _DXFOptions_variant:

-  ``variant`` :index:`: <pair: output - dxf - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

Used dicts
----------

- :ref:`CustomReport parameters <CustomReport>`
