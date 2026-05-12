.. _GerberOptions:

:orphan:


GerberOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~

-  **create_gerber_job_file** :index:`: <pair: output - gerber - options; create_gerber_job_file>` [:ref:`boolean <boolean>`] (default: ``true``) Creates a file with information about all the generated gerbers.
   You can use it in gerbview to load all gerbers at once.
-  **output** :index:`: <pair: output - gerber - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Output file name, the default KiCad name if empty.

.. note::
      KiCad will always create the file using its own name and then we can rename it. |br|
                   For this reason you must avoid generating two variants at the same directory when one of
                   them uses the default KiCad name. Affected by global options. |br|
..

-  **plot_sheet_reference** :index:`: <pair: output - gerber - options; plot_sheet_reference>` [:ref:`boolean <boolean>`] (default: ``false``) Include the frame and title block. Only available for KiCad 6+ and you get a poor result
   (i.e. always the default worksheet style, also problems expanding text variables). |br|
   The `pcb_print` output can do a better job for PDF, SVG, PS, EPS and PNG outputs.
-  **subtract_mask_from_silk** :index:`: <pair: output - gerber - options; subtract_mask_from_silk>` [:ref:`boolean <boolean>`] (default: ``false``) Subtract the solder mask from the silk screen.
-  **use_gerber_net_attributes** :index:`: <pair: output - gerber - options; use_gerber_net_attributes>` [:ref:`boolean <boolean>`] (default: ``true``) Include netlist metadata.
-  **use_gerber_x2_attributes** :index:`: <pair: output - gerber - options; use_gerber_x2_attributes>` [:ref:`boolean <boolean>`] (default: ``true``) Use the extended X2 format (otherwise use X1 formerly RS-274X).
-  **use_protel_extensions** :index:`: <pair: output - gerber - options; use_protel_extensions>` [:ref:`boolean <boolean>`] (default: ``false``) Use legacy Protel file extensions.

.. note::
      Inner layers numbering is different for KiCad 8 and 9. KiCad 8 starts numbering inner
                   layers with 2 and KiCad 9 with 1. |br|
..

-  ``custom_reports`` :index:`: <pair: output - gerber - options; custom_reports>`  [:ref:`CustomReport parameters <CustomReport>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) A list of customized reports for the manufacturer.
-  ``disable_aperture_macros`` :index:`: <pair: output - gerber - options; disable_aperture_macros>` [:ref:`boolean <boolean>`] (default: ``false``) Disable aperture macros (workaround for buggy CAM software) (KiCad 6).
-  ``dnf_filter`` :index:`: <pair: output - gerber - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``edge_cut_extension`` :index:`: <pair: output - gerber - options; edge_cut_extension>` [:ref:`string <string>`] (default: ``''``) Used to configure the edge cuts layer extension for Protel mode. Include the dot.
-  ``exclude_edge_layer`` :index:`: <pair: output - gerber - options; exclude_edge_layer>` [:ref:`boolean <boolean>`] (default: ``true``) Do not include the PCB edge layer.
-  ``exclude_filter`` :index:`: <pair: output - gerber - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_pads_from_silkscreen`` :index:`: <pair: output - gerber - options; exclude_pads_from_silkscreen>` [:ref:`boolean <boolean>`] (default: ``false``) Do not plot the component pads in the silk screen (KiCad 5.x only).
-  ``force_plot_invisible_refs_vals`` :index:`: <pair: output - gerber - options; force_plot_invisible_refs_vals>` [:ref:`boolean <boolean>`] (default: ``false``) Include references and values even when they are marked as invisible.
   Not available on KiCad 9.0.1 and newer.
-  ``gerber_job_file`` :index:`: <pair: output - gerber - options; gerber_job_file>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the gerber job file (%i='job', %x='gbrjob'). Affected by global options.
-  ``gerber_precision`` :index:`: <pair: output - gerber - options; gerber_precision>` [:ref:`number <number>`] (default: ``4.6``) (choices: 4.5, 4.6) This is the gerber coordinate format, can be 4.5 or 4.6.
-  ``inner_extension_pattern`` :index:`: <pair: output - gerber - options; inner_extension_pattern>` [:ref:`string <string>`] (default: ``''``) Used to change the Protel style extensions for inner layers.
   The replacement pattern can contain %n for the inner layer number and %N for the layer number. |br|
   Example '.g%n'. |br|

.. note::
      this numbering is consistent and the first inner layer is %n = 1 and %N = 2. Which
                   isn't true for KiCad. KiCad 8 uses 2 for the first inner and KiCad 9 uses 1. |br|
..

-  ``line_width`` :index:`: <pair: output - gerber - options; line_width>` [:ref:`number <number>`] (default: ``0.1``) (range: 0.02 to 2) Line_width for objects without width [mm] (KiCad 5).
-  ``plot_footprint_refs`` :index:`: <pair: output - gerber - options; plot_footprint_refs>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint references.
-  ``plot_footprint_values`` :index:`: <pair: output - gerber - options; plot_footprint_values>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint values.
-  ``pre_transform`` :index:`: <pair: output - gerber - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``sketch_pad_line_width`` :index:`: <pair: output - gerber - options; sketch_pad_line_width>` [:ref:`number <number>`] (default: ``0.1``) Line width for the sketched pads [mm], see `sketch_pads_on_fab_layers` (KiCad 6+)
   Note that this value is currently ignored by KiCad (6.0.9).
-  ``sketch_pads_on_fab_layers`` :index:`: <pair: output - gerber - options; sketch_pads_on_fab_layers>` [:ref:`boolean <boolean>`] (default: ``false``) Draw only the outline of the pads on the \\*.Fab layers (KiCad 6+).
-  ``tent_vias`` :index:`: <pair: output - gerber - options; tent_vias>` [:ref:`boolean <boolean>`] (default: ``true``) Cover the vias. Usable for KiCad versions older than 9.
   
.. warning::
   KiCad 8 has a bug that ignores this option. Set it from KiCad GUI.
..

-  ``uppercase_extensions`` :index:`: <pair: output - gerber - options; uppercase_extensions>` [:ref:`boolean <boolean>`] (default: ``false``) Use uppercase names for the extensions.
-  ``use_aux_axis_as_origin`` :index:`: <pair: output - gerber - options; use_aux_axis_as_origin>` [:ref:`boolean <boolean>`] (default: ``false``) Use the auxiliary axis as origin for coordinates.
-  ``variant`` :index:`: <pair: output - gerber - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

Used dicts
----------

- :ref:`CustomReport parameters <CustomReport>`
