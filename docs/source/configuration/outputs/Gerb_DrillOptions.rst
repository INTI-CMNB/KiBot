.. _Gerb_DrillOptions:

:orphan:


Gerb_DrillOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: output - gerb_drill - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) name for the drill file, KiCad defaults if empty (%i='PTH_drill'). Affected by global options.
-  ``dnf_filter`` :index:`: <pair: output - gerb_drill - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - gerb_drill - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``generate_drill_files`` :index:`: <pair: output - gerb_drill - options; generate_drill_files>` [:ref:`boolean <boolean>`] (default: ``true``) Generate drill files. Set to False and choose map format if only map is to be generated.
-  ``map`` :index:`: <pair: output - gerb_drill - options; map>`  [:ref:`DrillMap parameters <DrillMap>`] [:ref:`dict <dict>` | :ref:`string <string>`] (default: ``'None'``) (choices: "hpgl", "ps", "gerber", "dxf", "svg", "pdf", "None") Format for a graphical drill map.
   Not generated unless a format is specified. |br|
   KiCad 10 doesn't support HPGL.
-  ``npth_id`` :index:`: <pair: output - gerb_drill - options; npth_id>` [:ref:`string <string>`] Force this replacement for %i when generating NPTH files.
-  ``pre_transform`` :index:`: <pair: output - gerb_drill - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``pth_id`` :index:`: <pair: output - gerb_drill - options; pth_id>` [:ref:`string <string>`] Force this replacement for %i when generating PTH and unified files.
-  ``report`` :index:`: <pair: output - gerb_drill - options; report>`  [:ref:`DrillReport parameters <DrillReport>`] [:ref:`dict <dict>` | :ref:`string <string>`] (default: ``''``) Name of the drill report. Not generated unless a name is specified.
-  ``table`` :index:`: <pair: output - gerb_drill - options; table>`  [:ref:`DrillTable parameters <DrillTable>`] [:ref:`dict <dict>` | :ref:`string <string>`] (default: ``''``) Name of the drill table. Not generated unless a name is specified.
-  ``use_aux_axis_as_origin`` :index:`: <pair: output - gerb_drill - options; use_aux_axis_as_origin>` [:ref:`boolean <boolean>`] (default: ``false``) Use the auxiliary axis as origin for coordinates.
-  ``variant`` :index:`: <pair: output - gerb_drill - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Used for sub-PCBs.

Used dicts
----------

- :ref:`DrillMap parameters <DrillMap>`
- :ref:`DrillReport parameters <DrillReport>`
- :ref:`DrillTable parameters <DrillTable>`
