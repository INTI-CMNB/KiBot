.. _PanelizeFraming:

:orphan:


PanelizeFraming parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **type** :index:`: <pair: output - panelize - options - configs - framing; type>` ''
-  ``arg`` :index:`: <pair: output - panelize - options - configs - framing; arg>` [:ref:`string <string>`] (default: ``''``) Argument to pass to the plugin. Used for *plugin*.
-  ``chamfer`` :index:`: <pair: output - panelize - options - configs - framing; chamfer>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the size of chamfer frame corners. You can also separately specify `chamferwidth`
   and `chamferheight` to create a non 45 degrees chamfer.
-  *chamfer_height* :index:`: <pair: output - panelize - options - configs - framing; chamfer_height>` Alias for chamferheight.
-  *chamfer_width* :index:`: <pair: output - panelize - options - configs - framing; chamfer_width>` Alias for chamferwidth.
-  ``chamferheight`` :index:`: <pair: output - panelize - options - configs - framing; chamferheight>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Height of the chamfer frame corners, used for non 45 degrees chamfer.
-  ``chamferwidth`` :index:`: <pair: output - panelize - options - configs - framing; chamferwidth>` [:ref:`number <number>` | :ref:`string <string>`] Width of the chamfer frame corners, used for non 45 degrees chamfer.
-  ``code`` :index:`: <pair: output - panelize - options - configs - framing; code>` [:ref:`string <string>`] (default: ``''``) Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin*.
-  ``cuts`` :index:`: <pair: output - panelize - options - configs - framing; cuts>` [:ref:`string <string>`] (default: ``'both'``) (choices: "none", "both", "v", "h") Specify whether to add cuts to the corners of the frame for easy removal.
   Used for *frame*.
-  ``fillet`` :index:`: <pair: output - panelize - options - configs - framing; fillet>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify radius of fillet frame corners.
-  ``hspace`` :index:`: <pair: output - panelize - options - configs - framing; hspace>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``2``) Specify the horizontal space between PCB and the frame/rail.
-  *max_total_height* :index:`: <pair: output - panelize - options - configs - framing; max_total_height>` Alias for maxtotalheight.
-  *max_total_width* :index:`: <pair: output - panelize - options - configs - framing; max_total_width>` Alias for maxtotalwidth.
-  ``maxtotalheight`` :index:`: <pair: output - panelize - options - configs - framing; maxtotalheight>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``10000``) Maximal height of the panel.
-  ``maxtotalwidth`` :index:`: <pair: output - panelize - options - configs - framing; maxtotalwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``10000``) Maximal width of the panel.
-  *min_total_height* :index:`: <pair: output - panelize - options - configs - framing; min_total_height>` Alias for mintotalheight.
-  *min_total_width* :index:`: <pair: output - panelize - options - configs - framing; min_total_width>` Alias for mintotalwidth.
-  ``mintotalheight`` :index:`: <pair: output - panelize - options - configs - framing; mintotalheight>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) If needed, add extra material to the rail or frame to meet the minimal requested size.
   Useful for services that require minimal panel size.
-  ``mintotalwidth`` :index:`: <pair: output - panelize - options - configs - framing; mintotalwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) If needed, add extra material to the rail or frame to meet the minimal requested size.
   Useful for services that require minimal panel size.
-  *slot_width* :index:`: <pair: output - panelize - options - configs - framing; slot_width>` Alias for slotwidth.
-  ``slotwidth`` :index:`: <pair: output - panelize - options - configs - framing; slotwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``2``) Width of the milled slot for *tightframe*.
-  ``space`` :index:`: <pair: output - panelize - options - configs - framing; space>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``2``) Specify the space between PCB and the frame/rail. Overrides `hspace` and `vspace`.
-  ``vspace`` :index:`: <pair: output - panelize - options - configs - framing; vspace>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``2``) Specify the vertical space between PCB and the frame/rail.
-  ``width`` :index:`: <pair: output - panelize - options - configs - framing; width>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``5``) Specify with of the rails or frame.

