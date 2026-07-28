.. _DrillTable:

:orphan:


DrillTable parameters
~~~~~~~~~~~~~~~~~~~~~


.. _DrillTable_columns:

-  **columns** :index:`: <pair: output - gerb_drill - options - table; columns>`  [:ref:`DrillTableColumns parameters <DrillTableColumns>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>`] (default: ``['Count', 'Hole Size', 'Plated', 'Hole Shape', 'Drill Layer Pair', 'Hole Type']``) List of columns to display.
   Each entry can be a dictionary with `field`, `name` or just a string (field name).

.. _DrillTable_output:

-  **output** :index:`: <pair: output - gerb_drill - options - table; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name of the drill table. Not generated unless a name is specified.
   (%i='drill_table' %x='csv'). Affected by global options.

.. _DrillTable_units:

-  **units** :index:`: <pair: output - gerb_drill - options - table; units>` [:ref:`string <string>`] (default: ``'millimeters_mils'``) (choices: "millimeters", "mils", "millimeters_mils", "mils_millimeters") Units used for the hole sizes.

.. _DrillTable_group_slots_and_round_holes:

-  ``group_slots_and_round_holes`` :index:`: <pair: output - gerb_drill - options - table; group_slots_and_round_holes>` [:ref:`boolean <boolean>`] (default: ``true``) By default KiCad groups slots and rounded holes if they can be cut from the same tool (same diameter).

.. _DrillTable_unify_pth_and_npth:

-  ``unify_pth_and_npth`` :index:`: <pair: output - gerb_drill - options - table; unify_pth_and_npth>` [:ref:`string <string>`] (default: ``'auto'``) (choices: "yes", "no", "auto") Choose whether to unify plated and non-plated
   holes in the same table. If 'auto' is chosen, the setting is copied
   from the `excellon` output's `pth_and_npth_single_file`.

Used dicts
----------

- :ref:`DrillTableColumns parameters <DrillTableColumns>`
