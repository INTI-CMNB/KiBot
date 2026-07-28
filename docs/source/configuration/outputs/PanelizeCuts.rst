.. _PanelizeCuts:

:orphan:


PanelizeCuts parameters
~~~~~~~~~~~~~~~~~~~~~~~


.. _PanelizeCuts_type:

-  **type** :index:`: <pair: output - panelize - options - configs - cuts; type>` ''

.. _PanelizeCuts_arg:

-  ``arg`` :index:`: <pair: output - panelize - options - configs - cuts; arg>` [:ref:`string <string>`] (default: ``''``) Argument to pass to the plugin. Used for *plugin*.

.. _PanelizeCuts_clearance:

-  ``clearance`` :index:`: <pair: output - panelize - options - configs - cuts; clearance>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify clearance for copper around V-cuts.

.. _PanelizeCuts_code:

-  ``code`` :index:`: <pair: output - panelize - options - configs - cuts; code>` [:ref:`string <string>`] (default: ``''``) Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin*.

.. _PanelizeCuts_cut_curves:

-  *cut_curves* :index:`: <pair: output - panelize - options - configs - cuts; cut_curves>` Alias for cutcurves.

.. _PanelizeCuts_cutcurves:

-  ``cutcurves`` :index:`: <pair: output - panelize - options - configs - cuts; cutcurves>` [:ref:`boolean <boolean>`] (default: ``false``) Specify if curves should be approximated by straight cuts (e.g., for cutting tabs on circular boards).
   Used for *vcuts*.

.. _PanelizeCuts_drill:

-  ``drill`` :index:`: <pair: output - panelize - options - configs - cuts; drill>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.5``) Drill size used for the *mousebites*.

.. _PanelizeCuts_end_prolongation:

-  *end_prolongation* :index:`: <pair: output - panelize - options - configs - cuts; end_prolongation>` Alias for endprolongation.

.. _PanelizeCuts_endprolongation:

-  ``endprolongation`` :index:`: <pair: output - panelize - options - configs - cuts; endprolongation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) Prolongation on the end of V-CUT without text.

.. _PanelizeCuts_layer:

-  ``layer`` :index:`: <pair: output - panelize - options - configs - cuts; layer>` [:ref:`string <string>`] (default: ``'Cmts.User'``) Specify the layer to render V-cuts on. Also used for the *layer* type.

.. _PanelizeCuts_line_width:

-  *line_width* :index:`: <pair: output - panelize - options - configs - cuts; line_width>` Alias for linewidth.

.. _PanelizeCuts_linewidth:

-  ``linewidth`` :index:`: <pair: output - panelize - options - configs - cuts; linewidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.3``) Line width to plot cuts with.

.. _PanelizeCuts_offset:

-  ``offset`` :index:`: <pair: output - panelize - options - configs - cuts; offset>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the *mousebites* and *vcuts* offset, positive offset puts the cuts into the board,
   negative puts the cuts into the tabs.

.. _PanelizeCuts_prolong:

-  ``prolong`` :index:`: <pair: output - panelize - options - configs - cuts; prolong>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Distance for tangential prolongation of the cuts (to cut through the internal corner fillets
   caused by milling). Used for *mousebites* and *layer*.

.. _PanelizeCuts_spacing:

-  ``spacing`` :index:`: <pair: output - panelize - options - configs - cuts; spacing>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.8``) The spacing of the holes used for the *mousebites*.

.. _PanelizeCuts_template:

-  ``template`` :index:`: <pair: output - panelize - options - configs - cuts; template>` [:ref:`string <string>`] (default: ``'V-CUT'``) Text template for the V-CUT.

.. _PanelizeCuts_text_offset:

-  *text_offset* :index:`: <pair: output - panelize - options - configs - cuts; text_offset>` Alias for textoffset.

.. _PanelizeCuts_text_prolongation:

-  *text_prolongation* :index:`: <pair: output - panelize - options - configs - cuts; text_prolongation>` Alias for textprolongation.

.. _PanelizeCuts_text_size:

-  *text_size* :index:`: <pair: output - panelize - options - configs - cuts; text_size>` Alias for textsize.

.. _PanelizeCuts_text_thickness:

-  *text_thickness* :index:`: <pair: output - panelize - options - configs - cuts; text_thickness>` Alias for textthickness.

.. _PanelizeCuts_textoffset:

-  ``textoffset`` :index:`: <pair: output - panelize - options - configs - cuts; textoffset>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) Text offset from the V-CUT.

.. _PanelizeCuts_textprolongation:

-  ``textprolongation`` :index:`: <pair: output - panelize - options - configs - cuts; textprolongation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) Prolongation of the text size of V-CUT.

.. _PanelizeCuts_textsize:

-  ``textsize`` :index:`: <pair: output - panelize - options - configs - cuts; textsize>` [:ref:`number <number>` | :ref:`string <string>`] Text size for vcuts.

.. _PanelizeCuts_textthickness:

-  ``textthickness`` :index:`: <pair: output - panelize - options - configs - cuts; textthickness>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.3``) Text thickness for width.

