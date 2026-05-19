.. _BoMLinkableSimple:

:orphan:


BoMLinkableSimple parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **datasheet_as_link** :index:`: <pair: output - bom - options - json; datasheet_as_link>` [:ref:`string <string>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column with links to the datasheet.
-  **generate_dnf** :index:`: <pair: output - bom - options - json; generate_dnf>` [:ref:`boolean <boolean>`] (default: ``true``) Generate a separated section for DNF (Do Not Fit) components.
-  **logo** :index:`: <pair: output - bom - options - json; logo>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) PNG/SVG file to use as logo, use false to remove.
   Note that when using an SVG this is first converted to a PNG using `logo_width`.

-  **title** :index:`: <pair: output - bom - options - json; title>` [:ref:`string <string>`] (default: ``'KiBot Bill of Materials'``) BoM title.
-  ``digikey_link`` :index:`: <pair: output - bom - options - json; digikey_link>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing Digi-Key part numbers, will be linked to web page.

-  ``extra_info`` :index:`: <pair: output - bom - options - json; extra_info>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) Information to put after the title and before the pcb and stats info.

-  ``highlight_empty`` :index:`: <pair: output - bom - options - json; highlight_empty>` [:ref:`boolean <boolean>`] (default: ``true``) Use a color for empty cells. Applies only when `col_colors` is `true`.
-  ``lcsc_link`` :index:`: <pair: output - bom - options - json; lcsc_link>` [:ref:`boolean <boolean>` | :ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing LCSC part numbers, will be linked to web page.
   Use **true** to copy the value indicated by the `field_lcsc_part` global option.

-  ``logo_width`` :index:`: <pair: output - bom - options - json; logo_width>` [:ref:`number <number>`] (default: ``370``) Used when the logo is an SVG image. This width is used to render the SVG image.
-  ``mouser_link`` :index:`: <pair: output - bom - options - json; mouser_link>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing Mouser part numbers, will be linked to web page.


