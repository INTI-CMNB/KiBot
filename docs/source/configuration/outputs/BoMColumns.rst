.. _BoMColumns:

:orphan:


BoMColumns parameters
~~~~~~~~~~~~~~~~~~~~~


.. _BoMColumns_field:

-  **field** :index:`: <pair: output - bom - options - cost_extra_columns; field>` [:ref:`string <string>`] (default: ``''``) Name of the field to use for this column.
   Use `_field_lcsc_part` to get the value defined in the global options.

.. _BoMColumns_name:

-  **name** :index:`: <pair: output - bom - options - cost_extra_columns; name>` [:ref:`string <string>`] (default: ``''``) Name to display in the header. The field is used when empty.

.. _BoMColumns_comment:

-  ``comment`` :index:`: <pair: output - bom - options - cost_extra_columns; comment>` [:ref:`string <string>`] (default: ``''``) Used as explanation for this column. The XLSX output uses it.

.. _BoMColumns_join:

-  ``join`` :index:`: <pair: output - bom - options - cost_extra_columns; join>`  [:ref:`BoMJoinField parameters <BoMJoinField>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``''``) List of fields to join to this column.

.. _BoMColumns_level:

-  ``level`` :index:`: <pair: output - bom - options - cost_extra_columns; level>` [:ref:`number <number>`] (default: ``0``) Used to group columns. The XLSX output uses it to collapse columns.

Used dicts
----------

- :ref:`BoMJoinField parameters <BoMJoinField>`
