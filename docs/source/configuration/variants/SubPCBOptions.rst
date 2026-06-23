.. _SubPCBOptions:

:orphan:


SubPCBOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~


.. _SubPCBOptions_name:

-  **name** :index:`: <pair: variant - kicost - sub_pcbs; name>` [:ref:`string <string>`] (default: ``''``) Name for this sub-pcb.

.. _SubPCBOptions_ref:

-  *ref* :index:`: <pair: variant - kicost - sub_pcbs; ref>` Alias for reference.

.. _SubPCBOptions_reference:

-  **reference** :index:`: <pair: variant - kicost - sub_pcbs; reference>` [:ref:`string <string>`] (default: ``''``) Use it for the annotations method.
   This is the reference for the `kikit:Board` footprint used to identify the sub-PCB. |br|
   Note that you can use any footprint as long as its position is inside the PCB outline. |br|
   When empty the sub-PCB is specified using a rectangle.

.. _SubPCBOptions_bottom_right_x:

-  *bottom_right_x* :index:`: <pair: variant - kicost - sub_pcbs; bottom_right_x>` Alias for brx.

.. _SubPCBOptions_bottom_right_y:

-  *bottom_right_y* :index:`: <pair: variant - kicost - sub_pcbs; bottom_right_y>` Alias for bry.

.. _SubPCBOptions_brx:

-  ``brx`` :index:`: <pair: variant - kicost - sub_pcbs; brx>` [:ref:`number <number>` | :ref:`string <string>`] The X position of the bottom right corner for the rectangle that contains the sub-PCB.

.. _SubPCBOptions_bry:

-  ``bry`` :index:`: <pair: variant - kicost - sub_pcbs; bry>` [:ref:`number <number>` | :ref:`string <string>`] The Y position of the bottom right corner for the rectangle that contains the sub-PCB.

.. _SubPCBOptions_center_result:

-  ``center_result`` :index:`: <pair: variant - kicost - sub_pcbs; center_result>` [:ref:`boolean <boolean>`] (default: ``true``) Move the resulting PCB to the center of the page.
   You can disable it only for the internal tool, KiKit should always do it.

.. _SubPCBOptions_file_id:

-  ``file_id`` :index:`: <pair: variant - kicost - sub_pcbs; file_id>` [:ref:`string <string>`] (default: ``''``) Text to use as the replacement for %v expansion.
   When empty we use the parent `file_id` plus the `name` of the sub-PCB.

.. _SubPCBOptions_ref_layer:

-  ``ref_layer`` :index:`: <pair: variant - kicost - sub_pcbs; ref_layer>` [:ref:`string <string>`] (default: ``'Edge.Cuts'``) Layer where the PCB outline indicated by `reference` is found.
   So you can use an outline that is not the real PCB contour.

.. _SubPCBOptions_strip_annotation:

-  ``strip_annotation`` :index:`: <pair: variant - kicost - sub_pcbs; strip_annotation>` [:ref:`boolean <boolean>`] (default: ``false``) Remove the annotation footprint. Note that KiKit will remove all annotations,
   but the internal implementation just the one indicated by `ref`. |br|
   If you need to remove other annotations use an exclude filter.

.. _SubPCBOptions_tlx:

-  ``tlx`` :index:`: <pair: variant - kicost - sub_pcbs; tlx>` [:ref:`number <number>` | :ref:`string <string>`] The X position of the top left corner for the rectangle that contains the sub-PCB.

.. _SubPCBOptions_tly:

-  ``tly`` :index:`: <pair: variant - kicost - sub_pcbs; tly>` [:ref:`number <number>` | :ref:`string <string>`] The Y position of the top left corner for the rectangle that contains the sub-PCB.

.. _SubPCBOptions_tolerance:

-  ``tolerance`` :index:`: <pair: variant - kicost - sub_pcbs; tolerance>` [:ref:`number <number>` | :ref:`string <string>`] Used to enlarge the selected rectangle to include elements outside the board.
   KiCad 5: To avoid rounding issues this value is set to 0.000002 mm when 0 is specified.

.. _SubPCBOptions_tool:

-  ``tool`` :index:`: <pair: variant - kicost - sub_pcbs; tool>` [:ref:`string <string>`] (default: ``'internal'``) (choices: "internal", "kikit") Tool used to extract the sub-PCB..

.. _SubPCBOptions_top_left_x:

-  *top_left_x* :index:`: <pair: variant - kicost - sub_pcbs; top_left_x>` Alias for tlx.

.. _SubPCBOptions_top_left_y:

-  *top_left_y* :index:`: <pair: variant - kicost - sub_pcbs; top_left_y>` Alias for tly.

.. _SubPCBOptions_units:

-  ``units`` :index:`: <pair: variant - kicost - sub_pcbs; units>` [:ref:`string <string>`] (default: ``'mm'``) (choices: "millimeters", "inches", "mils", "mm", "cm", "dm", "m", "mil", "inch", "in") Units used when omitted.

