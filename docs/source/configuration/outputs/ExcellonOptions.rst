.. _ExcellonOptions:

:orphan:


ExcellonOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _ExcellonOptions_metric_units:

-  **metric_units** :index:`: <pair: output - excellon - options; metric_units>` [:ref:`boolean <boolean>`] (default: ``true``) Use metric units instead of inches.

.. _ExcellonOptions_mirror_y_axis:

-  **mirror_y_axis** :index:`: <pair: output - excellon - options; mirror_y_axis>` [:ref:`boolean <boolean>`] (default: ``false``) Invert the Y axis.

.. _ExcellonOptions_output:

-  **output** :index:`: <pair: output - excellon - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) name for the drill file, KiCad defaults if empty (%i='PTH_drill'). Affected by global options.

.. _ExcellonOptions_pth_and_npth_single_file:

-  **pth_and_npth_single_file** :index:`: <pair: output - excellon - options; pth_and_npth_single_file>` [:ref:`boolean <boolean>`] (default: ``true``) Generate one file for both, plated holes and non-plated holes, instead of two separated files.

.. _ExcellonOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - excellon - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _ExcellonOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - excellon - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _ExcellonOptions_generate_drill_files:

-  ``generate_drill_files`` :index:`: <pair: output - excellon - options; generate_drill_files>` [:ref:`boolean <boolean>`] (default: ``true``) Generate drill files. Set to False and choose map format if only map is to be generated.

.. _ExcellonOptions_left_digits:

-  ``left_digits`` :index:`: <pair: output - excellon - options; left_digits>` [:ref:`number <number>`] (default: ``0``) number of digits for integer part of coordinates (0 is auto).
   Doesn't apply to DECIMAL_FORMAT. |br|
   Default is 3 and currently can't be configured from the GUI, avoid using it.

.. _ExcellonOptions_map:

-  ``map`` :index:`: <pair: output - excellon - options; map>`  [:ref:`DrillMap parameters <DrillMap>`] [:ref:`dict <dict>` | :ref:`string <string>`] (default: ``'None'``) (choices: "hpgl", "ps", "gerber", "dxf", "svg", "pdf", "None") Format for a graphical drill map.
   Not generated unless a format is specified. |br|
   KiCad 10 doesn't support HPGL.

.. _ExcellonOptions_minimal_header:

-  ``minimal_header`` :index:`: <pair: output - excellon - options; minimal_header>` [:ref:`boolean <boolean>`] (default: ``false``) Use a minimal header in the file.

.. _ExcellonOptions_npth_id:

-  ``npth_id`` :index:`: <pair: output - excellon - options; npth_id>` [:ref:`string <string>`] Force this replacement for %i when generating NPTH files.

.. _ExcellonOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - excellon - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _ExcellonOptions_pth_id:

-  ``pth_id`` :index:`: <pair: output - excellon - options; pth_id>` [:ref:`string <string>`] Force this replacement for %i when generating PTH and unified files.

.. _ExcellonOptions_report:

-  ``report`` :index:`: <pair: output - excellon - options; report>`  [:ref:`DrillReport parameters <DrillReport>`] [:ref:`dict <dict>` | :ref:`string <string>`] (default: ``''``) Name of the drill report. Not generated unless a name is specified.

.. _ExcellonOptions_right_digits:

-  ``right_digits`` :index:`: <pair: output - excellon - options; right_digits>` [:ref:`number <number>`] (default: ``0``) number of digits for mantissa part of coordinates (0 is auto).
   Doesn't apply to DECIMAL_FORMAT. |br|
   Default is 3 and currently can't be configured from the GUI, avoid using it.

.. _ExcellonOptions_route_mode_for_oval_holes:

-  ``route_mode_for_oval_holes`` :index:`: <pair: output - excellon - options; route_mode_for_oval_holes>` [:ref:`boolean <boolean>`] (default: ``true``) Use route command for oval holes (G00), otherwise use G85.

.. _ExcellonOptions_table:

-  ``table`` :index:`: <pair: output - excellon - options; table>`  [:ref:`DrillTable parameters <DrillTable>`] [:ref:`dict <dict>` | :ref:`string <string>`] (default: ``''``) Name of the drill table. Not generated unless a name is specified.
   
.. note::
   if the PCB contains no drills the file won't be generated.
..


.. _ExcellonOptions_use_aux_axis_as_origin:

-  ``use_aux_axis_as_origin`` :index:`: <pair: output - excellon - options; use_aux_axis_as_origin>` [:ref:`boolean <boolean>`] (default: ``false``) Use the auxiliary axis as origin for coordinates.

.. _ExcellonOptions_variant:

-  ``variant`` :index:`: <pair: output - excellon - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Used for sub-PCBs.

.. _ExcellonOptions_zeros_format:

-  ``zeros_format`` :index:`: <pair: output - excellon - options; zeros_format>` [:ref:`string <string>`] (default: ``'DECIMAL_FORMAT'``) (choices: "DECIMAL_FORMAT", "SUPPRESS_LEADING", "SUPPRESS_TRAILING", "KEEP_ZEROS") How to handle the zeros.

Used dicts
----------

- :ref:`DrillMap parameters <DrillMap>`
- :ref:`DrillReport parameters <DrillReport>`
- :ref:`DrillTable parameters <DrillTable>`
