.. _ERCOptions_pre:

:orphan:


ERCOptions parameters
~~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: preflight - erc - erc; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated archive (%i=erc %x=according to format). Affected by global options.
-  ``category`` :index:`: <pair: preflight - erc - erc; category>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] The category for this preflight. If not specified an internally defined
   category is used. |br|
   Categories looks like file system paths, i.e. **PCB/fabrication/gerber**. |br|
   The categories are currently used for `navigate_results`.

-  ``dir`` :index:`: <pair: preflight - erc - erc; dir>` [:ref:`string <string>`] (default: ``''``) Sub-directory for the report.
-  ``dont_stop`` :index:`: <pair: preflight - erc - erc; dont_stop>` [:ref:`boolean <boolean>`] (default: ``false``) Continue even if we detect errors.
-  ``enabled`` :index:`: <pair: preflight - erc - erc; enabled>` [:ref:`boolean <boolean>`] (default: ``true``) Enable the check. This is the replacement for the boolean value.
-  ``filters`` :index:`: <pair: preflight - erc - erc; filters>`  [:ref:`FilterOptionsXRC parameters <FilterOptionsXRC_pre>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Used to manipulate the violations. Avoid using the *filters* preflight.
-  ``force_english`` :index:`: <pair: preflight - erc - erc; force_english>` [:ref:`boolean <boolean>`] (default: ``true``) Force english messages. KiCad 8.0.4 introduced translation, breaking filters for previous versions.
   Disable it if you prefer using the system wide language.
-  ``format`` :index:`: <pair: preflight - erc - erc; format>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'HTML'``) (choices: "RPT", "HTML", "CSV", "JSON") [:ref:`comma separated <comma_sep>`] Format/s used for the report.
   You can specify multiple formats.

-  ``units`` :index:`: <pair: preflight - erc - erc; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches", "mils") Units used for the positions. Affected by global options.
-  ``warnings_as_errors`` :index:`: <pair: preflight - erc - erc; warnings_as_errors>` [:ref:`boolean <boolean>`] (default: ``false``) Warnings are considered errors, they still reported as warnings.

Used dicts
----------

- :ref:`FilterOptionsXRC parameters <FilterOptionsXRC_pre>`
