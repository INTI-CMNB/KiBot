.. _BoMXLSX:

:orphan:


BoMXLSX parameters
~~~~~~~~~~~~~~~~~~

-  **datasheet_as_link** :index:`: <pair: output - bom - options - xlsx; datasheet_as_link>` [:ref:`string <string>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column with links to the datasheet.
-  **generate_dnf** :index:`: <pair: output - bom - options - xlsx; generate_dnf>` [:ref:`boolean <boolean>`] (default: ``true``) Generate a separated section for DNF (Do Not Fit) components.
-  **kicost** :index:`: <pair: output - bom - options - xlsx; kicost>` [:ref:`boolean <boolean>`] (default: ``false``) Enable KiCost worksheet creation.
   Note: an example of how to use it on CI/CD can be found `here <https://github.com/set-soft/kicost_ci_test>`__.
-  **logo** :index:`: <pair: output - bom - options - xlsx; logo>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) PNG/SVG file to use as logo, use false to remove.
   Note that when using an SVG this is first converted to a PNG using `logo_width`.

-  **specs** :index:`: <pair: output - bom - options - xlsx; specs>` [:ref:`boolean <boolean>`] (default: ``false``) Enable Specs worksheet creation. Contains specifications for the components.
   Works with only some KiCost APIs.
-  **title** :index:`: <pair: output - bom - options - xlsx; title>` [:ref:`string <string>`] (default: ``'KiBot Bill of Materials'``) BoM title.
-  ``col_colors`` :index:`: <pair: output - bom - options - xlsx; col_colors>` [:ref:`boolean <boolean>`] (default: ``true``) Use colors to show the field type.
-  ``digikey_link`` :index:`: <pair: output - bom - options - xlsx; digikey_link>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing Digi-Key part numbers, will be linked to web page.

-  ``extra_info`` :index:`: <pair: output - bom - options - xlsx; extra_info>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) Information to put after the title and before the pcb and stats info.

-  ``hide_pcb_info`` :index:`: <pair: output - bom - options - xlsx; hide_pcb_info>` [:ref:`boolean <boolean>`] (default: ``false``) Hide project information.
-  ``hide_stats_info`` :index:`: <pair: output - bom - options - xlsx; hide_stats_info>` [:ref:`boolean <boolean>`] (default: ``false``) Hide statistics information.
-  ``highlight_empty`` :index:`: <pair: output - bom - options - xlsx; highlight_empty>` [:ref:`boolean <boolean>`] (default: ``true``) Use a color for empty cells. Applies only when `col_colors` is `true`.
-  ``kicost_api_disable`` :index:`: <pair: output - bom - options - xlsx; kicost_api_disable>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] List of KiCost APIs to disable.

-  ``kicost_api_enable`` :index:`: <pair: output - bom - options - xlsx; kicost_api_enable>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] List of KiCost APIs to enable.

-  ``kicost_config`` :index:`: <pair: output - bom - options - xlsx; kicost_config>` [:ref:`string <string>`] (default: ``''``) KiCost configuration file. It contains the keys for the different distributors APIs.
   The regular KiCost config is used when empty. |br|
   Important for CI/CD environments: avoid exposing your API secrets!
   To understand how to achieve this, and also how to make use of the cache please visit the
   `kicost_ci_test <https://github.com/set-soft/kicost_ci_test>`__ repo.
-  ``kicost_dist_desc`` :index:`: <pair: output - bom - options - xlsx; kicost_dist_desc>` [:ref:`boolean <boolean>`] (default: ``false``) Used to add a column with the distributor's description. So you can check this is the right component.
-  ``lcsc_link`` :index:`: <pair: output - bom - options - xlsx; lcsc_link>` [:ref:`boolean <boolean>` | :ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing LCSC part numbers, will be linked to web page.
   Use **true** to copy the value indicated by the `field_lcsc_part` global option.

-  ``logo_scale`` :index:`: <pair: output - bom - options - xlsx; logo_scale>` [:ref:`number <number>`] (default: ``2``) Scaling factor for the logo. Note that this value isn't honored by all spreadsheet software.
-  ``logo_width`` :index:`: <pair: output - bom - options - xlsx; logo_width>` [:ref:`number <number>`] (default: ``370``) Used when the logo is an SVG image. This width is used to render the SVG image.
-  ``max_col_width`` :index:`: <pair: output - bom - options - xlsx; max_col_width>` [:ref:`number <number>`] (default: ``60``) (range: 20 to 999) Maximum column width (characters).
-  ``mouser_link`` :index:`: <pair: output - bom - options - xlsx; mouser_link>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`case insensitive <no_case>`]Column/s containing Mouser part numbers, will be linked to web page.

-  ``row_colors`` :index:`: <pair: output - bom - options - xlsx; row_colors>`  [:ref:`RowColors parameters <RowColors>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Used to highlight rows using filters. Rows that match a filter can be colored.
   Note that these rows won't have colored columns.
-  ``specs_columns`` :index:`: <pair: output - bom - options - xlsx; specs_columns>`  [:ref:`BoMColumns parameters <BoMColumns>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>`] (default: ``[]``) Which columns are included in the Specs worksheet. Use `References` for the
   references, 'Row' for the order and 'Sep' to separate groups at the same level. By default all are included. |br|
   Column names are distributor specific, the following aren't: '_desc', '_value', '_tolerance', '_footprint',
   '_power', '_current', '_voltage', '_frequency', '_temp_coeff', '_manf', '_size'. |br|
   Note that an empty list means all available specs, use `specs` options to disable it.
-  ``style`` :index:`: <pair: output - bom - options - xlsx; style>` [:ref:`string <string>`] (default: ``'modern-blue'``) Head style: modern-blue, modern-green, modern-red and classic.

Used dicts
----------

- :ref:`BoMColumns parameters <BoMColumns>`
- :ref:`RowColors parameters <RowColors>`
