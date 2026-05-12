.. _DRCOptions_pre:

:orphan:


DRCOptions parameters
~~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: preflight - drc - drc; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated archive (%i=drc %x=according to format). Affected by global options.
-  ``all_track_errors`` :index:`: <pair: preflight - drc - drc; all_track_errors>` [:ref:`boolean <boolean>`] (default: ``false``) Report all the errors for all the tracks, not just the first.
-  ``category`` :index:`: <pair: preflight - drc - drc; category>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] The category for this preflight. If not specified an internally defined
   category is used. |br|
   Categories looks like file system paths, i.e. **PCB/fabrication/gerber**. |br|
   The categories are currently used for `navigate_results`.

-  ``dir`` :index:`: <pair: preflight - drc - drc; dir>` [:ref:`string <string>`] (default: ``''``) Sub-directory for the report.
-  ``dont_stop`` :index:`: <pair: preflight - drc - drc; dont_stop>` [:ref:`boolean <boolean>`] (default: ``false``) Continue even if we detect errors.
-  ``enabled`` :index:`: <pair: preflight - drc - drc; enabled>` [:ref:`boolean <boolean>`] (default: ``true``) Enable the check. This is the replacement for the boolean value.
-  ``filters`` :index:`: <pair: preflight - drc - drc; filters>`  [:ref:`FilterOptionsXRC parameters <FilterOptionsXRC_pre>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Used to manipulate the violations. Avoid using the *filters* preflight.
-  ``force_english`` :index:`: <pair: preflight - drc - drc; force_english>` [:ref:`boolean <boolean>`] (default: ``true``) Force english messages. KiCad 8.0.4 introduced translation, breaking filters for previous versions.
   Disable it if you prefer using the system wide language.
-  ``format`` :index:`: <pair: preflight - drc - drc; format>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'HTML'``) (choices: "RPT", "HTML", "CSV", "JSON") [:ref:`comma separated <comma_sep>`] Format/s used for the report.
   You can specify multiple formats.

-  ``ignore_unconnected`` :index:`: <pair: preflight - drc - drc; ignore_unconnected>` [:ref:`boolean <boolean>`] (default: ``false``) Ignores the unconnected nets. Useful if you didn't finish the routing.
-  ``logo`` :index:`: <pair: preflight - drc - drc; logo>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) PNG file to use as logo, use false to remove.
   The KiBot logo is used by default.

-  ``logo_force_height`` :index:`: <pair: preflight - drc - drc; logo_force_height>` [:ref:`number <number>`] (default: ``-1``) Force logo height in px. Useful to get consistent heights across different logos..
-  ``logo_url`` :index:`: <pair: preflight - drc - drc; logo_url>` [:ref:`string <string>`] (default: ``'https://github.com/INTI-CMNB/KiBot/'``) Target link when clicking the logo.
-  ``schematic_parity`` :index:`: <pair: preflight - drc - drc; schematic_parity>` [:ref:`boolean <boolean>`] (default: ``true``) Check if the PCB and the schematic are coincident.
-  ``units`` :index:`: <pair: preflight - drc - drc; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches", "mils") Units used for the positions. Affected by global options.
-  ``warnings_as_errors`` :index:`: <pair: preflight - drc - drc; warnings_as_errors>` [:ref:`boolean <boolean>`] (default: ``false``) Warnings are considered errors, they still reported as warnings.

Used dicts
----------

- :ref:`FilterOptionsXRC parameters <FilterOptionsXRC_pre>`
