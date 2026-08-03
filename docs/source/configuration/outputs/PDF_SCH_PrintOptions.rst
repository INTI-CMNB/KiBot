.. _PDF_SCH_PrintOptions:

:orphan:


PDF_SCH_PrintOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _PDF_SCH_PrintOptions_frame:

-  **frame** :index:`: <pair: output - pdf_sch_print - options; frame>` [:ref:`boolean <boolean>`] (default: ``true``) Include the frame and title block.

.. _PDF_SCH_PrintOptions_all_pages:

-  ``all_pages`` :index:`: <pair: output - pdf_sch_print - options; all_pages>` [:ref:`boolean <boolean>`] (default: ``true``) Generate with all hierarchical sheets, unless `pages` is specified.

.. _PDF_SCH_PrintOptions_author:

-  ``author`` :index:`: <pair: output - pdf_sch_print - options; author>` [:ref:`string <string>`] (default: ``''``) Override the AUTHOR KiCad variable, used for PDF metadata.
   If blank the KiCad text variable is used.

.. _PDF_SCH_PrintOptions_background_color:

-  ``background_color`` :index:`: <pair: output - pdf_sch_print - options; background_color>` [:ref:`boolean <boolean>`] (default: ``false``) Use the background color from the `color_theme`.

.. _PDF_SCH_PrintOptions_color_theme:

-  ``color_theme`` :index:`: <pair: output - pdf_sch_print - options; color_theme>` [:ref:`string <string>`] (default: ``''``) Color theme used, this must exist in the KiCad config.

.. _PDF_SCH_PrintOptions_default_font:

-  ``default_font`` :index:`: <pair: output - pdf_sch_print - options; default_font>` [:ref:`string <string>`] (default: ``'KiCad Font'``) Name for the default font (KiCad 9+).

.. _PDF_SCH_PrintOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - pdf_sch_print - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PDF_SCH_PrintOptions_draw_hop_over:

-  ``draw_hop_over`` :index:`: <pair: output - pdf_sch_print - options; draw_hop_over>` [:ref:`boolean <boolean>`] (default: ``false``) Draw hop over at wire crossings (KiCad 10+)
   Note that you must have a project and the hop overs enabled in the GUI.

.. _PDF_SCH_PrintOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - pdf_sch_print - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PDF_SCH_PrintOptions_exclude_hierarchical_links:

-  ``exclude_hierarchical_links`` :index:`: <pair: output - pdf_sch_print - options; exclude_hierarchical_links>` [:ref:`boolean <boolean>`] (default: ``false``) Do not generate clickable links for hierarchical elements (KiCad 10+).

.. _PDF_SCH_PrintOptions_exclude_metadata:

-  ``exclude_metadata`` :index:`: <pair: output - pdf_sch_print - options; exclude_metadata>` [:ref:`boolean <boolean>`] (default: ``false``) Do not generate metadata from AUTHOR and SUBJECT KiCad variables.
   You can also use the `author` and `subject` options to define the metadata (KiCad 10+).

.. _PDF_SCH_PrintOptions_exclude_property_popups:

-  ``exclude_property_popups`` :index:`: <pair: output - pdf_sch_print - options; exclude_property_popups>` [:ref:`boolean <boolean>`] (default: ``false``) Do not generate property popups (KiCad 10+).

.. _PDF_SCH_PrintOptions_monochrome:

-  ``monochrome`` :index:`: <pair: output - pdf_sch_print - options; monochrome>` [:ref:`boolean <boolean>`] (default: ``false``) Generate a monochromatic output.

.. _PDF_SCH_PrintOptions_output:

-  ``output`` :index:`: <pair: output - pdf_sch_print - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output PDF (%i=schematic, %x=pdf). Affected by global options.

.. _PDF_SCH_PrintOptions_pages:

-  ``pages`` :index:`: <pair: output - pdf_sch_print - options; pages>` [:ref:`string <string>`] (default: ``''``) List of comma separarted pages to print. Ranges are allowed i.e.: `3-5` or `3-` or `-3`.

.. _PDF_SCH_PrintOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - pdf_sch_print - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _PDF_SCH_PrintOptions_sheet_reference_layout:

-  ``sheet_reference_layout`` :index:`: <pair: output - pdf_sch_print - options; sheet_reference_layout>` [:ref:`string <string>`] (default: ``''``) Worksheet file (.kicad_wks) to use. Leave empty to use the one specified in the project.
   This option works only when you print the toplevel sheet of a project and the project
   file is available.

.. _PDF_SCH_PrintOptions_subject:

-  ``subject`` :index:`: <pair: output - pdf_sch_print - options; subject>` [:ref:`string <string>`] (default: ``''``) Override the SUBJECT KiCad variable, used for PDF metadata.
   If blank the KiCad text variable is used.

.. _PDF_SCH_PrintOptions_title:

-  ``title`` :index:`: <pair: output - pdf_sch_print - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.

.. _PDF_SCH_PrintOptions_title_propagate:

-  ``title_propagate`` :index:`: <pair: output - pdf_sch_print - options; title_propagate>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled we also set the title for all the sub-sheets.

.. _PDF_SCH_PrintOptions_variant:

-  ``variant`` :index:`: <pair: output - pdf_sch_print - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Not fitted components are crossed.

