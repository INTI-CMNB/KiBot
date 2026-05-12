.. _IncludeTableOptions:

:orphan:


IncludeTableOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **outputs** :index:`: <pair: output - pcb_print - options - include_table; outputs>`  [:ref:`IncTableOutputOptions parameters <IncTableOutputOptions>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: computed for your project) List of CSV-generating outputs.
   When empty we include all possible outputs.
-  ``enabled`` :index:`: <pair: output - pcb_print - options - include_table; enabled>` [:ref:`boolean <boolean>`] (default: ``true``) Enable the check. This is the replacement for the boolean value.
-  ``format_drill_table`` :index:`: <pair: output - pcb_print - options - include_table; format_drill_table>` [:ref:`boolean <boolean>`] (default: ``true``) If True, CSV drill tables will have drill marks displayed on the left and
   an extra bottom rule for the total number of holes.
-  ``group_name`` :index:`: <pair: output - pcb_print - options - include_table; group_name>` [:ref:`string <string>`] (default: ``'kibot_table'``) Name for the group containing the table. The name of the group
   should be <group_name>_X where X is the output name. |br|
   When the output generates more than one CSV use *kibot_table_out[2]*
   to select the second CSV. Python expressions for slicing are supported,
   for example *kibot_table_out[:10]* would include all elements until the 10th
   element (10th excluded), and *kibot_table_out[2][5:8]* would include the second
   output's elements number 6 to 8 (python indexes start at 0). |br|.

Used dicts
----------

- :ref:`IncTableOutputOptions parameters <IncTableOutputOptions>`
