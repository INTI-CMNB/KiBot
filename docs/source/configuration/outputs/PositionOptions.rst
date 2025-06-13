.. _PositionOptions:


PositionOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **format** :index:`: <pair: output - position - options; format>` [:ref:`string <string>`] (default: ``'ASCII'``) (choices: "ASCII", "CSV", "GBR") Format for the position file.
   Note that the gerber format (GBR) needs KiCad 7+ and doesn't support most of the options. |br|
   Only the options that explicitly say the format is supported.
-  **only_smd** :index:`: <pair: output - position - options; only_smd>` [:ref:`boolean <boolean>`] (default: ``true``) Only include the surface mount components.
-  **output** :index:`: <pair: output - position - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Output file name (%i='top_pos'|'bottom_pos'|'both_pos', %x='pos'|'csv'|'gbr').
   
.. note::
   when using separate files you must use `%i` to differentiate them. Affected by global options.
..

-  **separate_files_for_front_and_back** :index:`: <pair: output - position - options; separate_files_for_front_and_back>` [:ref:`boolean <boolean>`] (default: ``true``) Generate two separated files, one for the top and another for the bottom.
-  **units** :index:`: <pair: output - position - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches", "mils") Units used for the positions. Affected by global options.
-  ``bottom_negative_x`` :index:`: <pair: output - position - options; bottom_negative_x>` [:ref:`boolean <boolean>`] (default: ``false``) Use negative X coordinates for footprints on bottom layer.
-  ``columns`` :index:`: <pair: output - position - options; columns>`  [:ref:`PosColumns parameters <PosColumns>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>`] (default: ``['Ref', 'Val', 'Package', 'PosX', 'PosY', 'Rot', 'Side']``) Which columns are included in the output.
-  ``dnf_filter`` :index:`: <pair: output - position - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - position - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``gerber_board_edge`` :index:`: <pair: output - position - options; gerber_board_edge>` [:ref:`boolean <boolean>`] (default: ``false``) Include the board edge in the gerber output.
-  ``include_virtual`` :index:`: <pair: output - position - options; include_virtual>` [:ref:`boolean <boolean>`] (default: ``false``) Include virtual components. For special purposes, not pick & place.
   Note that virtual components is a KiCad 5 concept. |br|
   For KiCad 6+ we replace this concept by the option to exclude from position file.
-  ``pre_transform`` :index:`: <pair: output - position - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``quote_all`` :index:`: <pair: output - position - options; quote_all>` [:ref:`boolean <boolean>`] (default: ``false``) When generating the CSV quote all values, even numbers.
-  ``right_digits`` :index:`: <pair: output - position - options; right_digits>` [:ref:`number <number>`] (default: ``4``) number of digits for mantissa part of coordinates (0 is auto).
-  ``separator`` :index:`: <pair: output - position - options; separator>` [:ref:`string <string>`] (default: ``','``) CSV Separator. Only used for CSV format.
   Only one character can be specified.
-  ``use_aux_axis_as_origin`` :index:`: <pair: output - position - options; use_aux_axis_as_origin>` [:ref:`boolean <boolean>`] (default: ``true``) Use the auxiliary axis as origin for coordinates (KiCad default).
   Supported by the gerber format.
-  ``variant`` :index:`: <pair: output - position - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

.. toctree::
   :caption: Used dicts

   PosColumns
