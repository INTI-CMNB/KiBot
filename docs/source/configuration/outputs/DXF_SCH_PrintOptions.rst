.. _DXF_SCH_PrintOptions:

:orphan:


DXF_SCH_PrintOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _DXF_SCH_PrintOptions_frame:

-  **frame** :index:`: <pair: output - dxf_sch_print - options; frame>` [:ref:`boolean <boolean>`] (default: ``true``) Include the frame and title block.

.. _DXF_SCH_PrintOptions_all_pages:

-  ``all_pages`` :index:`: <pair: output - dxf_sch_print - options; all_pages>` [:ref:`boolean <boolean>`] (default: ``true``) Generate with all hierarchical sheets, unless `pages` is specified.

.. _DXF_SCH_PrintOptions_background_color:

-  ``background_color`` :index:`: <pair: output - dxf_sch_print - options; background_color>` [:ref:`boolean <boolean>`] (default: ``false``) Use the background color from the `color_theme` (KiCad 6).

.. _DXF_SCH_PrintOptions_color_theme:

-  ``color_theme`` :index:`: <pair: output - dxf_sch_print - options; color_theme>` [:ref:`string <string>`] (default: ``''``) Color theme used, this must exist in the KiCad config (KiCad 6).

.. _DXF_SCH_PrintOptions_default_font:

-  ``default_font`` :index:`: <pair: output - dxf_sch_print - options; default_font>` [:ref:`string <string>`] (default: ``'KiCad Font'``) Name for the default font. Only for KiCad 9 and newer.

.. _DXF_SCH_PrintOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - dxf_sch_print - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _DXF_SCH_PrintOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - dxf_sch_print - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _DXF_SCH_PrintOptions_monochrome:

-  ``monochrome`` :index:`: <pair: output - dxf_sch_print - options; monochrome>` [:ref:`boolean <boolean>`] (default: ``false``) Generate a monochromatic output.

.. _DXF_SCH_PrintOptions_output:

-  ``output`` :index:`: <pair: output - dxf_sch_print - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output DXF (%i=schematic, %x=dxf). Affected by global options.

.. _DXF_SCH_PrintOptions_pages:

-  ``pages`` :index:`: <pair: output - dxf_sch_print - options; pages>` [:ref:`string <string>`] (default: ``''``) List of comma separarted pages to print. Ranges are allowed i.e.: `3-5` or `3-` or `-3`.

.. _DXF_SCH_PrintOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - dxf_sch_print - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _DXF_SCH_PrintOptions_sheet_reference_layout:

-  ``sheet_reference_layout`` :index:`: <pair: output - dxf_sch_print - options; sheet_reference_layout>` [:ref:`string <string>`] (default: ``''``) Worksheet file (.kicad_wks) to use. Leave empty to use the one specified in the project.
   This option works only when you print the toplevel sheet of a project and the project
   file is available.

.. _DXF_SCH_PrintOptions_title:

-  ``title`` :index:`: <pair: output - dxf_sch_print - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.

.. _DXF_SCH_PrintOptions_title_propagate:

-  ``title_propagate`` :index:`: <pair: output - dxf_sch_print - options; title_propagate>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled we also set the title for all the sub-sheets.

.. _DXF_SCH_PrintOptions_variant:

-  ``variant`` :index:`: <pair: output - dxf_sch_print - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Not fitted components are crossed.

