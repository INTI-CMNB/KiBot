.. _DrillOptions:

:orphan:


DrillOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~


.. _DrillOptions_group_slots_and_round_holes:

-  ``group_slots_and_round_holes`` :index:`: <pair: output - pcb_print - options - drill; group_slots_and_round_holes>` [:ref:`boolean <boolean>`] (default: ``true``) By default KiCad groups slots and rounded holes if they can be cut from the same tool (same diameter).

.. _DrillOptions_unify_pth_and_npth:

-  ``unify_pth_and_npth`` :index:`: <pair: output - pcb_print - options - drill; unify_pth_and_npth>` [:ref:`string <string>`] (default: ``'auto'``) (choices: "yes", "no", "auto") Choose whether to unify plated and non-plated
   holes in the same table. If 'auto' is chosen, the setting is copied
   from the `excellon` output's `pth_and_npth_single_file`.

