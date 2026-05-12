.. _PDF_PCB_PrintOptions:

:orphan:


PDF_PCB_PrintOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **plot_sheet_reference** :index:`: <pair: output - pdf_pcb_print - options; plot_sheet_reference>` [:ref:`boolean <boolean>`] (default: ``true``) Include the title-block.
-  **scaling** :index:`: <pair: output - pdf_pcb_print - options; scaling>` [:ref:`number <number>`] (default: ``1.0``) Scale factor (0 means autoscaling). You should disable `plot_sheet_reference` when using it.
-  **separated** :index:`: <pair: output - pdf_pcb_print - options; separated>` [:ref:`boolean <boolean>`] (default: ``false``) Print layers in separated pages.
-  ``color_theme`` :index:`: <pair: output - pdf_pcb_print - options; color_theme>` [:ref:`string <string>`] (default: ``'_builtin_classic'``) Selects the color theme. Onlyu applies to KiCad 6.
   To use the KiCad 6 default colors select `_builtin_default`. |br|
   Usually user colors are stored as `user`, but you can give it another name.
-  ``dnf_filter`` :index:`: <pair: output - pdf_pcb_print - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``drill_marks`` :index:`: <pair: output - pdf_pcb_print - options; drill_marks>` [:ref:`string <string>`] (default: ``'full'``) (choices: "none", "small", "full") What to use to indicate the drill places, can be none, small or full (for real scale).
-  ``exclude_filter`` :index:`: <pair: output - pdf_pcb_print - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``force_edge_cuts`` :index:`: <pair: output - pdf_pcb_print - options; force_edge_cuts>` [:ref:`boolean <boolean>`] (default: ``true``) Only useful for KiCad 6 when printing in one page, you can disable the edge here.
   KiCad 5 forces it by default, and you can't control it from config files. |br|
   Same for KiCad 6 when printing to separated pages.
-  ``hide_excluded`` :index:`: <pair: output - pdf_pcb_print - options; hide_excluded>` [:ref:`boolean <boolean>`] (default: ``false``) Hide components in the Fab layer that are marked as excluded by a variant.
   Affected by global options.
-  ``mirror`` :index:`: <pair: output - pdf_pcb_print - options; mirror>` [:ref:`boolean <boolean>`] (default: ``false``) Print mirrored (X axis inverted). ONLY for KiCad 6.
-  ``monochrome`` :index:`: <pair: output - pdf_pcb_print - options; monochrome>` [:ref:`boolean <boolean>`] (default: ``false``) Print in black and white.
-  ``output`` :index:`: <pair: output - pdf_pcb_print - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output PDF (%i=layers, %x=pdf). Affected by global options.
-  *output_name* :index:`: <pair: output - pdf_pcb_print - options; output_name>` Alias for output.
-  ``pre_transform`` :index:`: <pair: output - pdf_pcb_print - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``title`` :index:`: <pair: output - pdf_pcb_print - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.
-  ``variant`` :index:`: <pair: output - pdf_pcb_print - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

