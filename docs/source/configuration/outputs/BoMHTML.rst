.. _BoMHTML:

:orphan:


BoMHTML parameters
~~~~~~~~~~~~~~~~~~


.. _BoMHTML_datasheet_as_link:

-  **datasheet_as_link** :index:`: <pair: output - bom - options - html; datasheet_as_link>` [:ref:`string <string>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column with links to the datasheet.

.. _BoMHTML_generate_dnf:

-  **generate_dnf** :index:`: <pair: output - bom - options - html; generate_dnf>` [:ref:`boolean <boolean>`] (default: ``true``) Generate a separated section for DNF (Do Not Fit) components.

.. _BoMHTML_logo:

-  **logo** :index:`: <pair: output - bom - options - html; logo>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) PNG/SVG file to use as logo, use false to remove.
   Note that when using an SVG this is first converted to a PNG using `logo_width`.


.. _BoMHTML_title:

-  **title** :index:`: <pair: output - bom - options - html; title>` [:ref:`string <string>`] (default: ``'KiBot Bill of Materials'``) BoM title.

.. _BoMHTML_col_colors:

-  ``col_colors`` :index:`: <pair: output - bom - options - html; col_colors>` [:ref:`boolean <boolean>`] (default: ``true``) Use colors to show the field type.

.. _BoMHTML_digikey_link:

-  ``digikey_link`` :index:`: <pair: output - bom - options - html; digikey_link>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing Digi-Key part numbers, will be linked to web page.


.. _BoMHTML_extra_info:

-  ``extra_info`` :index:`: <pair: output - bom - options - html; extra_info>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) Information to put after the title and before the pcb and stats info.


.. _BoMHTML_hide_pcb_info:

-  ``hide_pcb_info`` :index:`: <pair: output - bom - options - html; hide_pcb_info>` [:ref:`boolean <boolean>`] (default: ``false``) Hide project information.

.. _BoMHTML_hide_stats_info:

-  ``hide_stats_info`` :index:`: <pair: output - bom - options - html; hide_stats_info>` [:ref:`boolean <boolean>`] (default: ``false``) Hide statistics information.

.. _BoMHTML_highlight_empty:

-  ``highlight_empty`` :index:`: <pair: output - bom - options - html; highlight_empty>` [:ref:`boolean <boolean>`] (default: ``true``) Use a color for empty cells. Applies only when `col_colors` is `true`.

.. _BoMHTML_lcsc_link:

-  ``lcsc_link`` :index:`: <pair: output - bom - options - html; lcsc_link>` [:ref:`boolean <boolean>` | :ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing LCSC part numbers, will be linked to web page.
   Use **true** to copy the value indicated by the `field_lcsc_part` global option.


.. _BoMHTML_logo_width:

-  ``logo_width`` :index:`: <pair: output - bom - options - html; logo_width>` [:ref:`number <number>`] (default: ``370``) Used when the logo is an SVG image. This width is used to render the SVG image.

.. _BoMHTML_mouser_link:

-  ``mouser_link`` :index:`: <pair: output - bom - options - html; mouser_link>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing Mouser part numbers, will be linked to web page.


.. _BoMHTML_row_colors:

-  ``row_colors`` :index:`: <pair: output - bom - options - html; row_colors>`  [:ref:`RowColors parameters <RowColors>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Used to highlight rows using filters. Rows that match a filter can be colored.
   Note that these rows won't have colored columns.

.. _BoMHTML_style:

-  ``style`` :index:`: <pair: output - bom - options - html; style>` [:ref:`string <string>`] (default: ``'modern-blue'``) Page style. Internal styles: modern-blue, modern-green, modern-red and classic.
   Or you can provide a CSS file name. Please use .css as file extension. |br|.

Used dicts
----------

- :ref:`RowColors parameters <RowColors>`
