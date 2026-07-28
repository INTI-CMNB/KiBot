.. _DrawStackupOptions_pre:

:orphan:


DrawStackupOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _DrawStackupOptions_columns:

-  **columns** :index:`: <pair: preflight - draw_stackup - draw_stackup; columns>`  [:ref:`SUColumns parameters <SUColumns_pre>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>`] (default: computed for your project) List of columns to display.
   Can be just the name of the column. |br|
   Available columns are *gerber*, *drawing*, *thickness* and *description*. |br|
   When empty KiBot will add them in the above order, skipping the *gerber* if not available.

.. _DrawStackupOptions_gerber:

-  **gerber** :index:`: <pair: preflight - draw_stackup - draw_stackup; gerber>` [:ref:`string <string>`] (default: ``''``) Name of the output used to generate the gerbers. This is needed only when you
   want to include the *gerber* column, containing the gerber file names.

.. _DrawStackupOptions_border:

-  ``border`` :index:`: <pair: preflight - draw_stackup - draw_stackup; border>` [:ref:`number <number>`] (default: ``0.1``) Line width for the border box. Use 0 to eliminate it.

.. _DrawStackupOptions_enabled:

-  ``enabled`` :index:`: <pair: preflight - draw_stackup - draw_stackup; enabled>` [:ref:`boolean <boolean>`] (default: ``true``) Enable the check. This is the replacement for the boolean value.

.. _DrawStackupOptions_group_name:

-  ``group_name`` :index:`: <pair: preflight - draw_stackup - draw_stackup; group_name>` [:ref:`string <string>`] (default: ``'kibot_stackup'``) Name for the group containing the drawings. If KiBot can't find it will create
   a new group at the specified coordinates for the indicated layer.

.. _DrawStackupOptions_height:

-  ``height`` :index:`: <pair: preflight - draw_stackup - draw_stackup; height>` [:ref:`number <number>`] (default: ``100``) Height for the drawing. The units are defined by the global *units* variable.
   Only used when the group can't be found.

.. _DrawStackupOptions_layer:

-  ``layer`` :index:`: <pair: preflight - draw_stackup - draw_stackup; layer>` [:ref:`string <string>`] (default: ``'Cmts.User'``) Layer used for the stackup. Only used when the group can't be found.
   Otherwise we use the layer for the first object in the group.

.. _DrawStackupOptions_pos_x:

-  ``pos_x`` :index:`: <pair: preflight - draw_stackup - draw_stackup; pos_x>` [:ref:`number <number>`] (default: ``19``) X position in the PCB. The units are defined by the global *units* variable.
   Only used when the group can't be found.

.. _DrawStackupOptions_pos_y:

-  ``pos_y`` :index:`: <pair: preflight - draw_stackup - draw_stackup; pos_y>` [:ref:`number <number>`] (default: ``100``) Y position in the PCB. The units are defined by the global *units* variable.
   Only used when the group can't be found.

.. _DrawStackupOptions_width:

-  ``width`` :index:`: <pair: preflight - draw_stackup - draw_stackup; width>` [:ref:`number <number>`] (default: ``120``) Width for the drawing. The units are defined by the global *units* variable.
   Only used when the group can't be found.

Used dicts
----------

- :ref:`SUColumns parameters <SUColumns_pre>`
