.. _PanelizePost:

:orphan:


PanelizePost parameters
~~~~~~~~~~~~~~~~~~~~~~~


.. _PanelizePost_copperfill:

-  ``copperfill`` :index:`: <pair: output - panelize - options - configs - post; copperfill>` [:ref:`boolean <boolean>`] (default: ``false``) Fill tabs and frame with copper (e.g., to save etchant or to increase rigidity of flex-PCB panels).

.. _PanelizePost_dimensions:

-  ``dimensions`` :index:`: <pair: output - panelize - options - configs - post; dimensions>` [:ref:`boolean <boolean>`] (default: ``false``) Draw dimensions with the panel size..

.. _PanelizePost_edge_width:

-  *edge_width* :index:`: <pair: output - panelize - options - configs - post; edge_width>` Alias for edgewidth.

.. _PanelizePost_edgewidth:

-  ``edgewidth`` :index:`: <pair: output - panelize - options - configs - post; edgewidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.1``) Specify line width for the Edge.Cuts of the panel.

.. _PanelizePost_mill_radius:

-  *mill_radius* :index:`: <pair: output - panelize - options - configs - post; mill_radius>` Alias for millradius.

.. _PanelizePost_mill_radius_outer:

-  *mill_radius_outer* :index:`: <pair: output - panelize - options - configs - post; mill_radius_outer>` Alias for millradiusouter.

.. _PanelizePost_millradius:

-  ``millradius`` :index:`: <pair: output - panelize - options - configs - post; millradius>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Simulate the milling operation (add fillets to the internal corners).
   Specify mill radius (usually 1 mm). 0 radius disables the functionality.

.. _PanelizePost_millradiusouter:

-  ``millradiusouter`` :index:`: <pair: output - panelize - options - configs - post; millradiusouter>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Like `millradius`, but modifies only board outer counter.
   No internal features of the board are affected.

.. _PanelizePost_origin:

-  ``origin`` :index:`: <pair: output - panelize - options - configs - post; origin>` [:ref:`string <string>`] (default: ``'tl'``) (choices: "tl", "tr", "bl", "br", "mt", "mb", "ml", "mr", "c") Specify if the auxiliary origin and grid origin should be replaced.
   Can be one of tl, tr, bl, br (corners), mt, mb, ml, mr (middle of sides), c (center). |br|
   Empty string does not changes the origin.

.. _PanelizePost_reconstruct_arcs:

-  *reconstruct_arcs* :index:`: <pair: output - panelize - options - configs - post; reconstruct_arcs>` Alias for reconstructarcs.

.. _PanelizePost_reconstructarcs:

-  ``reconstructarcs`` :index:`: <pair: output - panelize - options - configs - post; reconstructarcs>` [:ref:`boolean <boolean>`] (default: ``false``) The panelization process works on top of a polygonal representation of the board.
   This options allows to reconstruct the arcs in the design before saving the panel.

.. _PanelizePost_refill_zones:

-  *refill_zones* :index:`: <pair: output - panelize - options - configs - post; refill_zones>` Alias for refillzones.

.. _PanelizePost_refillzones:

-  ``refillzones`` :index:`: <pair: output - panelize - options - configs - post; refillzones>` [:ref:`boolean <boolean>`] (default: ``false``) Refill the user zones after the panel is build.
   This is only necessary when you want your zones to avoid cuts in panel.

.. _PanelizePost_script:

-  ``script`` :index:`: <pair: output - panelize - options - configs - post; script>` [:ref:`string <string>`] (default: ``''``) A path to custom Python file. The file should contain a function kikitPostprocess(panel, args) that
   receives the prepared panel as the kikit.panelize.Panel object and the user-supplied arguments as a
   string - see :ref:`scriptarg <PanelizePost_scriptarg>`. The function can make arbitrary changes to the panel - you can append text,
   footprints, alter labels, etc. The function is invoked after the whole panel is constructed
   (including all other postprocessing). If you try to add a functionality for a common fabrication
   houses via scripting, consider submitting PR for KiKit.

.. _PanelizePost_script_arg:

-  *script_arg* :index:`: <pair: output - panelize - options - configs - post; script_arg>` Alias for scriptarg.

.. _PanelizePost_scriptarg:

-  ``scriptarg`` :index:`: <pair: output - panelize - options - configs - post; scriptarg>` [:ref:`string <string>`] (default: ``''``) An arbitrary string passed to the user post-processing script specified in script.

.. _PanelizePost_type:

-  **type** :index:`: <pair: output - panelize - options - configs - post; type>` ''

