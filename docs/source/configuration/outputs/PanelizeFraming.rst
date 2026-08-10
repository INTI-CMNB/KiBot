.. _PanelizeFraming:

:orphan:


PanelizeFraming parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _PanelizeFraming_type:

-  **type** :index:`: <pair: output - panelize - options - configs - framing; type>` ''

.. _PanelizeFraming_arg:

-  ``arg`` :index:`: <pair: output - panelize - options - configs - framing; arg>` [:ref:`string <string>`] (default: ``''``) Argument to pass to the plugin. Used for *plugin*.

.. _PanelizeFraming_chamfer:

-  ``chamfer`` :index:`: <pair: output - panelize - options - configs - framing; chamfer>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the size of chamfer frame corners. You can also separately specify `chamferwidth`
   and `chamferheight` to create a non 45 degrees chamfer.

.. _PanelizeFraming_chamfer_height:

-  *chamfer_height* :index:`: <pair: output - panelize - options - configs - framing; chamfer_height>` Alias for chamferheight.

.. _PanelizeFraming_chamfer_width:

-  *chamfer_width* :index:`: <pair: output - panelize - options - configs - framing; chamfer_width>` Alias for chamferwidth.

.. _PanelizeFraming_chamferheight:

-  ``chamferheight`` :index:`: <pair: output - panelize - options - configs - framing; chamferheight>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Height of the chamfer frame corners, used for non 45 degrees chamfer.

.. _PanelizeFraming_chamferwidth:

-  ``chamferwidth`` :index:`: <pair: output - panelize - options - configs - framing; chamferwidth>` [:ref:`number <number>` | :ref:`string <string>`] Width of the chamfer frame corners, used for non 45 degrees chamfer.

.. _PanelizeFraming_code:

-  ``code`` :index:`: <pair: output - panelize - options - configs - framing; code>` [:ref:`string <string>`] (default: ``''``) Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin*.

.. _PanelizeFraming_cuts:

-  ``cuts`` :index:`: <pair: output - panelize - options - configs - framing; cuts>` [:ref:`string <string>`] (default: ``'both'``) (choices: "none", "both", "v", "h") Specify whether to add cuts to the corners of the frame for easy removal.
   Used for *frame*.

.. _PanelizeFraming_fillet:

-  ``fillet`` :index:`: <pair: output - panelize - options - configs - framing; fillet>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify radius of fillet frame corners.

.. _PanelizeFraming_hspace:

-  ``hspace`` :index:`: <pair: output - panelize - options - configs - framing; hspace>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``2``) Specify the horizontal space between PCB and the frame/rail.

.. _PanelizeFraming_max_total_height:

-  *max_total_height* :index:`: <pair: output - panelize - options - configs - framing; max_total_height>` Alias for maxtotalheight.

.. _PanelizeFraming_max_total_width:

-  *max_total_width* :index:`: <pair: output - panelize - options - configs - framing; max_total_width>` Alias for maxtotalwidth.

.. _PanelizeFraming_maxtotalheight:

-  ``maxtotalheight`` :index:`: <pair: output - panelize - options - configs - framing; maxtotalheight>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``10000``) Maximal height of the panel.

.. _PanelizeFraming_maxtotalwidth:

-  ``maxtotalwidth`` :index:`: <pair: output - panelize - options - configs - framing; maxtotalwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``10000``) Maximal width of the panel.

.. _PanelizeFraming_min_total_height:

-  *min_total_height* :index:`: <pair: output - panelize - options - configs - framing; min_total_height>` Alias for mintotalheight.

.. _PanelizeFraming_min_total_width:

-  *min_total_width* :index:`: <pair: output - panelize - options - configs - framing; min_total_width>` Alias for mintotalwidth.

.. _PanelizeFraming_mintotalheight:

-  ``mintotalheight`` :index:`: <pair: output - panelize - options - configs - framing; mintotalheight>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) If needed, add extra material to the rail or frame to meet the minimal requested size.
   Useful for services that require minimal panel size.

.. _PanelizeFraming_mintotalwidth:

-  ``mintotalwidth`` :index:`: <pair: output - panelize - options - configs - framing; mintotalwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) If needed, add extra material to the rail or frame to meet the minimal requested size.
   Useful for services that require minimal panel size.

.. _PanelizeFraming_slot_width:

-  *slot_width* :index:`: <pair: output - panelize - options - configs - framing; slot_width>` Alias for slotwidth.

.. _PanelizeFraming_slotwidth:

-  ``slotwidth`` :index:`: <pair: output - panelize - options - configs - framing; slotwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``2``) Width of the milled slot for *tightframe*.

.. _PanelizeFraming_space:

-  ``space`` :index:`: <pair: output - panelize - options - configs - framing; space>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``2``) Specify the space between PCB and the frame/rail. Overrides `hspace` and `vspace`.

.. _PanelizeFraming_vspace:

-  ``vspace`` :index:`: <pair: output - panelize - options - configs - framing; vspace>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``2``) Specify the vertical space between PCB and the frame/rail.

.. _PanelizeFraming_widenercorners:

-  ``widenercorners`` :index:`: <pair: output - panelize - options - configs - framing; widenercorners>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] [tl,tr,bl,br] List of rail/frame outer corners where a rail widener
   patch is added. A widener is a solid patch of extra rail material used to give pick-and-place
   photoelectric sensors a bigger flat target. It never grows the panel's outer outline and never overlaps
   an actual board: the patch is clipped against the board outline(s) if it would otherwise reach that far. |br|
   Only valid for `type` *railstb*, *railslr*, *frame* and *tightframe*. Implemented as a `plugin`: setting
   this option makes KiBot overwrite `type`, `code` and `arg` with its own values, so none of them can be
   explicitly specified (i.e. you can't combine the widener with another custom `plugin`).


.. _PanelizeFraming_widenergap:

-  ``widenergap`` :index:`: <pair: output - panelize - options - configs - framing; widenergap>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Minimum gap kept between the rail widener patch and the board(s). When 0 (the default)
   the frame's own `hspace`/`vspace` (whichever applies to the widener's growth direction) is used instead. |br|
   Automatically increased by `tabs.fillet` internally, to counteract KiKit's own reverse-tab-fillet pass
   which would otherwise round the patch into the board and eat into this gap.

.. _PanelizeFraming_widenerlength:

-  ``widenerlength`` :index:`: <pair: output - panelize - options - configs - framing; widenerlength>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Length of the rail widener patch along the rail edge.

.. _PanelizeFraming_widenerwidth:

-  ``widenerwidth`` :index:`: <pair: output - panelize - options - configs - framing; widenerwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Depth of the rail widener patch, i.e. how far it reaches from the panel's outer edge
   towards the board. Can exceed the rail/frame `width`; it's only clipped if it would overlap a board.

.. _PanelizeFraming_width:

-  ``width`` :index:`: <pair: output - panelize - options - configs - framing; width>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``5``) Specify with of the rails or frame.

