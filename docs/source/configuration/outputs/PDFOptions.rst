.. _PDFOptions:

:orphan:


PDFOptions parameters
~~~~~~~~~~~~~~~~~~~~~


.. _PDFOptions_output:

-  **output** :index:`: <pair: output - pdf - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Output file name, the default KiCad name if empty.

.. note::
   KiCad will always create the file using its own name and then we can rename it. |br|
   For this reason you must avoid generating two variants at the same directory when one of
   them uses the default KiCad name. Affected by global options. |br|
..


.. _PDFOptions_plot_sheet_reference:

-  **plot_sheet_reference** :index:`: <pair: output - pdf - options; plot_sheet_reference>` [:ref:`boolean <boolean>`] (default: ``false``) Include the frame and title block. Only available for KiCad 6+ and you get a poor result
   (i.e. always the default worksheet style, also problems expanding text variables). |br|
   The `pcb_print` output can do a better job for PDF, SVG, PS, EPS and PNG outputs.

.. _PDFOptions_scaling:

-  **scaling** :index:`: <pair: output - pdf - options; scaling>` [:ref:`number <number>`] (default: ``1``) Scale factor (0 means autoscaling).

.. _PDFOptions_subtract_mask_from_silk:

-  **subtract_mask_from_silk** :index:`: <pair: output - pdf - options; subtract_mask_from_silk>` [:ref:`boolean <boolean>`] (default: ``false``) Subtract the solder mask from the silk screen.

.. _PDFOptions_author:

-  ``author`` :index:`: <pair: output - pdf - options; author>` [:ref:`string <string>`] (default: ``''``) Override the AUTHOR KiCad variable, used for PDF metadata. (KiCad 11+)
   If blank the KiCad text variable is used.

.. _PDFOptions_back_footprint_property_popups:

-  ``back_footprint_property_popups`` :index:`: <pair: output - pdf - options; back_footprint_property_popups>` [:ref:`boolean <boolean>`] (default: ``true``) Include footprint property popups for the back side (KiCad 11+).

.. _PDFOptions_background_color:

-  ``background_color`` :index:`: <pair: output - pdf - options; background_color>` [:ref:`string <string>`] (default: ``''``) Color for the background (KiCad 11+).

.. _PDFOptions_color_theme:

-  ``color_theme`` :index:`: <pair: output - pdf - options; color_theme>` [:ref:`string <string>`] (default: ``'_builtin_classic'``) Selects the color theme (KiCad 11+).

.. _PDFOptions_custom_reports:

-  ``custom_reports`` :index:`: <pair: output - pdf - options; custom_reports>`  [:ref:`CustomReport parameters <CustomReport>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) A list of customized reports for the manufacturer.

.. _PDFOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - pdf - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PDFOptions_drill_marks:

-  ``drill_marks`` :index:`: <pair: output - pdf - options; drill_marks>` [:ref:`string <string>`] (default: ``'full'``) (choices: "none", "small", "full") What to use to indicate the drill places, can be none, small or full (for real scale).

.. _PDFOptions_edge_cut_extension:

-  ``edge_cut_extension`` :index:`: <pair: output - pdf - options; edge_cut_extension>` [:ref:`string <string>`] (default: ``''``) Used to configure the edge cuts layer extension for Protel mode. Include the dot.

.. _PDFOptions_exclude_edge_layer:

-  ``exclude_edge_layer`` :index:`: <pair: output - pdf - options; exclude_edge_layer>` [:ref:`boolean <boolean>`] (default: ``true``) Do not include the PCB edge layer.

.. _PDFOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - pdf - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PDFOptions_exclude_metadata:

-  ``exclude_metadata`` :index:`: <pair: output - pdf - options; exclude_metadata>` [:ref:`boolean <boolean>`] (default: ``false``) Do not generate metadata from AUTHOR and SUBJECT KiCad variables.
   You can also use the `author` and `subject` options to define the metadata (KiCad 11+).

.. _PDFOptions_force_plot_invisible_refs_vals:

-  ``force_plot_invisible_refs_vals`` :index:`: <pair: output - pdf - options; force_plot_invisible_refs_vals>` [:ref:`boolean <boolean>`] (default: ``false``) Include references and values even when they are marked as invisible.
   Not available on KiCad 9.0.1 and newer.

.. _PDFOptions_front_footprint_property_popups:

-  ``front_footprint_property_popups`` :index:`: <pair: output - pdf - options; front_footprint_property_popups>` [:ref:`boolean <boolean>`] (default: ``true``) Include footprint property popups for the front side (KiCad 11+).

.. _PDFOptions_individual_page_scaling:

-  ``individual_page_scaling`` :index:`: <pair: output - pdf - options; individual_page_scaling>` [:ref:`boolean <boolean>`] (default: ``true``) Tell KiCad to apply the scaling for each layer as a separated entity.
   Disabling it the pages are coherent and can be superposed (KiCad <11).

.. _PDFOptions_inner_extension_pattern:

-  ``inner_extension_pattern`` :index:`: <pair: output - pdf - options; inner_extension_pattern>` [:ref:`string <string>`] (default: ``''``) Used to change the Protel style extensions for inner layers.
   The replacement pattern can contain %n for the inner layer number and %N for the layer number. |br|
   Example '.g%n'. |br|

.. note::
   this numbering is consistent and the first inner layer is %n = 1 and %N = 2. Which
   isn't true for KiCad. KiCad 8 uses 2 for the first inner and KiCad 9 uses 1. |br|
..


.. _PDFOptions_mirror_plot:

-  ``mirror_plot`` :index:`: <pair: output - pdf - options; mirror_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Plot mirrored.

.. _PDFOptions_monochrome:

-  ``monochrome`` :index:`: <pair: output - pdf - options; monochrome>` [:ref:`boolean <boolean>`] (default: ``true``) Black and white output (KiCad 11+).

.. _PDFOptions_negative_plot:

-  ``negative_plot`` :index:`: <pair: output - pdf - options; negative_plot>` [:ref:`boolean <boolean>`] (default: ``false``) Invert black and white.

.. _PDFOptions_plot_footprint_refs:

-  ``plot_footprint_refs`` :index:`: <pair: output - pdf - options; plot_footprint_refs>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint references.

.. _PDFOptions_plot_footprint_values:

-  ``plot_footprint_values`` :index:`: <pair: output - pdf - options; plot_footprint_values>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint values.

.. _PDFOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - pdf - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PDFOptions_single_file:

-  ``single_file`` :index:`: <pair: output - pdf - options; single_file>` [:ref:`boolean <boolean>`] (default: ``false``) Plot all the pages to a single file, see :ref:`single_page <PDFOptions_single_page>` (KiCad 11+).

.. _PDFOptions_single_page:

-  ``single_page`` :index:`: <pair: output - pdf - options; single_page>` [:ref:`boolean <boolean>`] (default: ``false``) Plot all the layers in a single page when `single_file` is enabled (KiCad 11+).

.. _PDFOptions_sketch_pad_line_width:

-  ``sketch_pad_line_width`` :index:`: <pair: output - pdf - options; sketch_pad_line_width>` [:ref:`number <number>`] (default: ``0.1``) Line width for the sketched pads [mm], see :ref:`sketch_pads_on_fab_layers <PDFOptions_sketch_pads_on_fab_layers>` (KiCad 6.0.0 to 6.0.8).

.. _PDFOptions_sketch_pad_numbers:

-  ``sketch_pad_numbers`` :index:`: <pair: output - pdf - options; sketch_pad_numbers>` [:ref:`boolean <boolean>`] (default: ``false``) Plot pad numbers on top of sketched pads on the \\*.Fab layers (KiCad 11+).

.. _PDFOptions_sketch_pads_on_fab_layers:

-  ``sketch_pads_on_fab_layers`` :index:`: <pair: output - pdf - options; sketch_pads_on_fab_layers>` [:ref:`boolean <boolean>`] (default: ``false``) Draw only the outline of the pads on the \\*.Fab layers (KiCad 6+).

.. _PDFOptions_subject:

-  ``subject`` :index:`: <pair: output - pdf - options; subject>` [:ref:`string <string>`] (default: ``''``) Override the SUBJECT KiCad variable, used for PDF metadata. (KiCad 11+)
   If blank the KiCad text variable is used.

.. _PDFOptions_tent_vias:

-  ``tent_vias`` :index:`: <pair: output - pdf - options; tent_vias>` [:ref:`boolean <boolean>`] (default: ``true``) Cover the vias. Usable for KiCad versions older than 9.
   
.. warning::
   KiCad 8 has a bug that ignores this option. Set it from KiCad GUI.
..


.. _PDFOptions_uppercase_extensions:

-  ``uppercase_extensions`` :index:`: <pair: output - pdf - options; uppercase_extensions>` [:ref:`boolean <boolean>`] (default: ``false``) Use uppercase names for the extensions.

.. _PDFOptions_variant:

-  ``variant`` :index:`: <pair: output - pdf - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

Used dicts
----------

- :ref:`CustomReport parameters <CustomReport>`
