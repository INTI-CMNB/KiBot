.. _SVGOptions:

:orphan:


SVGOptions parameters
~~~~~~~~~~~~~~~~~~~~~


.. _SVGOptions_output:

-  **output** :index:`: <pair: output - svg - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Output file name, the default KiCad name if empty.

.. note::
   KiCad will always create the file using its own name and then we can rename it. |br|
   For this reason you must avoid generating two variants at the same directory when one of
   them uses the default KiCad name. Affected by global options. |br|
..


.. _SVGOptions_plot_sheet_reference:

-  **plot_sheet_reference** :index:`: <pair: output - svg - options; plot_sheet_reference>` [:ref:`boolean <boolean>`] (default: ``false``) Include the frame and title block. Only available for KiCad 6+ and you get a poor result
   (i.e. always the default worksheet style, also problems expanding text variables). |br|
   The `pcb_print` output can do a better job for PDF, SVG, PS, EPS and PNG outputs.

.. _SVGOptions_scaling:

-  **scaling** :index:`: <pair: output - svg - options; scaling>` [:ref:`number <number>`] (default: ``1``) Scale factor (0 means autoscaling).

.. _SVGOptions_custom_reports:

-  ``custom_reports`` :index:`: <pair: output - svg - options; custom_reports>`  [:ref:`CustomReport parameters <CustomReport>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) A list of customized reports for the manufacturer.

.. _SVGOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - svg - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _SVGOptions_drill_marks:

-  ``drill_marks`` :index:`: <pair: output - svg - options; drill_marks>` [:ref:`string <string>`] (default: ``'full'``) (choices: "none", "small", "full") What to use to indicate the drill places, can be none, small or full (for real scale).

.. _SVGOptions_edge_cut_extension:

-  ``edge_cut_extension`` :index:`: <pair: output - svg - options; edge_cut_extension>` [:ref:`string <string>`] (default: ``''``) Used to configure the edge cuts layer extension for Protel mode. Include the dot.

.. _SVGOptions_exclude_edge_layer:

-  ``exclude_edge_layer`` :index:`: <pair: output - svg - options; exclude_edge_layer>` [:ref:`boolean <boolean>`] (default: ``true``) Do not include the PCB edge layer.

.. _SVGOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - svg - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _SVGOptions_exclude_pads_from_silkscreen:

-  ``exclude_pads_from_silkscreen`` :index:`: <pair: output - svg - options; exclude_pads_from_silkscreen>` [:ref:`boolean <boolean>`] (default: ``false``) Do not plot the component pads in the silk screen (KiCad 5.x only).

.. _SVGOptions_force_plot_invisible_refs_vals:

-  ``force_plot_invisible_refs_vals`` :index:`: <pair: output - svg - options; force_plot_invisible_refs_vals>` [:ref:`boolean <boolean>`] (default: ``false``) Include references and values even when they are marked as invisible.
   Not available on KiCad 9.0.1 and newer.

.. _SVGOptions_individual_page_scaling:

-  ``individual_page_scaling`` :index:`: <pair: output - svg - options; individual_page_scaling>` [:ref:`boolean <boolean>`] (default: ``true``) Tell KiCad to apply the scaling for each layer as a separated entity.
   Disabling it the pages are coherent and can be superposed.

.. _SVGOptions_inner_extension_pattern:

-  ``inner_extension_pattern`` :index:`: <pair: output - svg - options; inner_extension_pattern>` [:ref:`string <string>`] (default: ``''``) Used to change the Protel style extensions for inner layers.
   The replacement pattern can contain %n for the inner layer number and %N for the layer number. |br|
   Example '.g%n'. |br|

.. note::
   this numbering is consistent and the first inner layer is %n = 1 and %N = 2. Which
   isn't true for KiCad. KiCad 8 uses 2 for the first inner and KiCad 9 uses 1. |br|
..


.. _SVGOptions_limit_viewbox:

-  ``limit_viewbox`` :index:`: <pair: output - svg - options; limit_viewbox>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled the view box is limited to a selected area.
   This option can't be enabled when using a scale.

.. _SVGOptions_line_width:

-  ``line_width`` :index:`: <pair: output - svg - options; line_width>` [:ref:`number <number>`] (default: ``0.25``) (range: 0.02 to 2) For objects without width [mm] (KiCad 5).

.. _SVGOptions_margin:

-  ``margin`` :index:`: <pair: output - svg - options; margin>`  [:ref:`PcbMargin parameters <PcbMargin>`] [:ref:`number <number>` | :ref:`dict <dict>`] (default: ``0``) Margin around the view box [mm].
   Using a number the margin is the same in the four directions. |br|
   See :ref:`limit_viewbox <SVGOptions_limit_viewbox>` option.

.. _SVGOptions_mirror_plot:

-  ``mirror_plot`` :index:`: <pair: output - svg - options; mirror_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Plot mirrored.

.. _SVGOptions_negative_plot:

-  ``negative_plot`` :index:`: <pair: output - svg - options; negative_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Invert black and white.

.. _SVGOptions_plot_footprint_refs:

-  ``plot_footprint_refs`` :index:`: <pair: output - svg - options; plot_footprint_refs>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint references.

.. _SVGOptions_plot_footprint_values:

-  ``plot_footprint_values`` :index:`: <pair: output - svg - options; plot_footprint_values>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint values.

.. _SVGOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - svg - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _SVGOptions_size_detection:

-  ``size_detection`` :index:`: <pair: output - svg - options; size_detection>` [:ref:`string <string>`] (default: ``'kicad_edge'``) (choices: "kicad_edge", "kicad_all") Method used to detect the size of the view box.
   The `kicad_edge` method uses the size of the board as reported by KiCad,
   components that extend beyond the PCB limit will be cropped. You can manually
   adjust the margin to make them visible. |br|
   The `kicad_all` method uses the whole size reported by KiCad. Usually includes extra space. |br|
   See :ref:`limit_viewbox <SVGOptions_limit_viewbox>` option.

.. _SVGOptions_sketch_pad_line_width:

-  ``sketch_pad_line_width`` :index:`: <pair: output - svg - options; sketch_pad_line_width>` [:ref:`number <number>`] (default: ``0.1``) Line width for the sketched pads [mm], see :ref:`sketch_pads_on_fab_layers <SVGOptions_sketch_pads_on_fab_layers>` (KiCad 6+)
   Note that this value is currently ignored by KiCad (6.0.9).

.. _SVGOptions_sketch_pads_on_fab_layers:

-  ``sketch_pads_on_fab_layers`` :index:`: <pair: output - svg - options; sketch_pads_on_fab_layers>` [:ref:`boolean <boolean>`] (default: ``false``) Draw only the outline of the pads on the \\*.Fab layers (KiCad 6+).

.. _SVGOptions_svg_precision:

-  ``svg_precision`` :index:`: <pair: output - svg - options; svg_precision>` [:ref:`number <number>`] (default: ``4``) (range: 0 to 6) Scale factor used to represent 1 mm in the SVG (KiCad 6).
   The value is how much zeros has the multiplier (1 mm = 10 power `svg_precision` units). |br|
   Note that for an A4 paper Firefox 91 and Chrome 105 can't handle more than 5.

.. _SVGOptions_tent_vias:

-  ``tent_vias`` :index:`: <pair: output - svg - options; tent_vias>` [:ref:`boolean <boolean>`] (default: ``true``) Cover the vias. Usable for KiCad versions older than 9.
   
.. warning::
   KiCad 8 has a bug that ignores this option. Set it from KiCad GUI.
..


.. _SVGOptions_uppercase_extensions:

-  ``uppercase_extensions`` :index:`: <pair: output - svg - options; uppercase_extensions>` [:ref:`boolean <boolean>`] (default: ``false``) Use uppercase names for the extensions.

.. _SVGOptions_use_aux_axis_as_origin:

-  ``use_aux_axis_as_origin`` :index:`: <pair: output - svg - options; use_aux_axis_as_origin>` [:ref:`boolean <boolean>`] (default: ``false``) Use the auxiliary axis as origin for coordinates.

.. _SVGOptions_variant:

-  ``variant`` :index:`: <pair: output - svg - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

Used dicts
----------

- :ref:`CustomReport parameters <CustomReport>`
- :ref:`PcbMargin parameters <PcbMargin>`
