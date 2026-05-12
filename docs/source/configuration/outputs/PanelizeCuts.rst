.. _PanelizeCuts:

:orphan:


PanelizeCuts parameters
~~~~~~~~~~~~~~~~~~~~~~~

-  **type** :index:`: <pair: output - panelize - options - configs - cuts; type>` ''
-  ``arg`` :index:`: <pair: output - panelize - options - configs - cuts; arg>` [:ref:`string <string>`] (default: ``''``) Argument to pass to the plugin. Used for *plugin*.
-  ``clearance`` :index:`: <pair: output - panelize - options - configs - cuts; clearance>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify clearance for copper around V-cuts.
-  ``code`` :index:`: <pair: output - panelize - options - configs - cuts; code>` [:ref:`string <string>`] (default: ``''``) Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin*.
-  *cut_curves* :index:`: <pair: output - panelize - options - configs - cuts; cut_curves>` Alias for cutcurves.
-  ``cutcurves`` :index:`: <pair: output - panelize - options - configs - cuts; cutcurves>` [:ref:`boolean <boolean>`] (default: ``false``) Specify if curves should be approximated by straight cuts (e.g., for cutting tabs on circular boards).
   Used for *vcuts*.
-  ``drill`` :index:`: <pair: output - panelize - options - configs - cuts; drill>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.5``) Drill size used for the *mousebites*.
-  *end_prolongation* :index:`: <pair: output - panelize - options - configs - cuts; end_prolongation>` Alias for endprolongation.
-  ``endprolongation`` :index:`: <pair: output - panelize - options - configs - cuts; endprolongation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) Prolongation on the end of V-CUT without text.
-  ``layer`` :index:`: <pair: output - panelize - options - configs - cuts; layer>` [:ref:`string <string>`] (default: ``'Cmts.User'``) Specify the layer to render V-cuts on. Also used for the *layer* type.
-  *line_width* :index:`: <pair: output - panelize - options - configs - cuts; line_width>` Alias for linewidth.
-  ``linewidth`` :index:`: <pair: output - panelize - options - configs - cuts; linewidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.3``) Line width to plot cuts with.
-  ``offset`` :index:`: <pair: output - panelize - options - configs - cuts; offset>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the *mousebites* and *vcuts* offset, positive offset puts the cuts into the board,
   negative puts the cuts into the tabs.
-  ``prolong`` :index:`: <pair: output - panelize - options - configs - cuts; prolong>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Distance for tangential prolongation of the cuts (to cut through the internal corner fillets
   caused by milling). Used for *mousebites* and *layer*.
-  ``spacing`` :index:`: <pair: output - panelize - options - configs - cuts; spacing>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.8``) The spacing of the holes used for the *mousebites*.
-  ``template`` :index:`: <pair: output - panelize - options - configs - cuts; template>` [:ref:`string <string>`] (default: ``'V-CUT'``) Text template for the V-CUT.
-  *text_offset* :index:`: <pair: output - panelize - options - configs - cuts; text_offset>` Alias for textoffset.
-  *text_prolongation* :index:`: <pair: output - panelize - options - configs - cuts; text_prolongation>` Alias for textprolongation.
-  *text_size* :index:`: <pair: output - panelize - options - configs - cuts; text_size>` Alias for textsize.
-  *text_thickness* :index:`: <pair: output - panelize - options - configs - cuts; text_thickness>` Alias for textthickness.
-  ``textoffset`` :index:`: <pair: output - panelize - options - configs - cuts; textoffset>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) Text offset from the V-CUT.
-  ``textprolongation`` :index:`: <pair: output - panelize - options - configs - cuts; textprolongation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) Prolongation of the text size of V-CUT.
-  ``textsize`` :index:`: <pair: output - panelize - options - configs - cuts; textsize>` [:ref:`number <number>` | :ref:`string <string>`] Text size for vcuts.
-  ``textthickness`` :index:`: <pair: output - panelize - options - configs - cuts; textthickness>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.3``) Text thickness for width.

