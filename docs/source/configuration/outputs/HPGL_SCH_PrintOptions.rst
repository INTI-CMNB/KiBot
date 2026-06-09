.. _HPGL_SCH_PrintOptions:

:orphan:


HPGL_SCH_PrintOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **frame** :index:`: <pair: output - hpgl_sch_print - options; frame>` [:ref:`boolean <boolean>`] (default: ``true``) Include the frame and title block.
-  ``all_pages`` :index:`: <pair: output - hpgl_sch_print - options; all_pages>` [:ref:`boolean <boolean>`] (default: ``true``) Generate with all hierarchical sheets, unless `pages` is specified.
-  ``background_color`` :index:`: <pair: output - hpgl_sch_print - options; background_color>` [:ref:`boolean <boolean>`] (default: ``false``) Use the background color from the `color_theme` (KiCad 6).
-  ``color_theme`` :index:`: <pair: output - hpgl_sch_print - options; color_theme>` [:ref:`string <string>`] (default: ``''``) Color theme used, this must exist in the KiCad config (KiCad 6).
-  ``default_font`` :index:`: <pair: output - hpgl_sch_print - options; default_font>` [:ref:`string <string>`] (default: ``'KiCad Font'``) Name for the default font. Only for KiCad 9 and newer.
-  ``dnf_filter`` :index:`: <pair: output - hpgl_sch_print - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - hpgl_sch_print - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``monochrome`` :index:`: <pair: output - hpgl_sch_print - options; monochrome>` [:ref:`boolean <boolean>`] (default: ``false``) Generate a monochromatic output.
-  ``origin`` :index:`: <pair: output - hpgl_sch_print - options; origin>` [:ref:`string <string>`] (default: ``'bottom_left'``) (choices: "bottom_left", "centered", "page_fit", "content_fit") Origin and scale.
-  ``output`` :index:`: <pair: output - hpgl_sch_print - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output HPGL (%i=schematic, %x=plt). Affected by global options.
-  ``pages`` :index:`: <pair: output - hpgl_sch_print - options; pages>` [:ref:`string <string>`] (default: ``''``) List of comma separarted pages to print. Ranges are allowed i.e.: `3-5` or `3-` or `-3`.
-  ``pen_size`` :index:`: <pair: output - hpgl_sch_print - options; pen_size>` [:ref:`number <number>`] (default: ``0.4826``) Pen size (diameter) [mm].
-  ``pre_transform`` :index:`: <pair: output - hpgl_sch_print - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``sheet_reference_layout`` :index:`: <pair: output - hpgl_sch_print - options; sheet_reference_layout>` [:ref:`string <string>`] (default: ``''``) Worksheet file (.kicad_wks) to use. Leave empty to use the one specified in the project.
   This option works only when you print the toplevel sheet of a project and the project
   file is available.
-  ``title`` :index:`: <pair: output - hpgl_sch_print - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.
-  ``title_propagate`` :index:`: <pair: output - hpgl_sch_print - options; title_propagate>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled we also set the title for all the sub-sheets.
-  ``variant`` :index:`: <pair: output - hpgl_sch_print - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Not fitted components are crossed.

