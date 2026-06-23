.. _PanelizeText:

:orphan:


PanelizeText parameters
~~~~~~~~~~~~~~~~~~~~~~~


.. _PanelizeText_text:

-  **text** :index:`: <pair: output - panelize - options - configs - text4; text>` [:ref:`string <string>`] (default: ``''``) The text to be displayed. Note that you can escape ; via \\.
   Available variables in text: *date* formats current date as <year>-<month>-<day>,
   *time24* formats current time in 24-hour format,
   *boardTitle* the title from the source board,
   *boardDate* the date from the source board,
   *boardRevision* the revision from the source board,
   *boardCompany* the company from the source board,
   *boardComment1*-*boardComment9* comments from the source board.

.. _PanelizeText_type:

-  **type** :index:`: <pair: output - panelize - options - configs - text4; type>` ''

.. _PanelizeText_anchor:

-  ``anchor`` :index:`: <pair: output - panelize - options - configs - text4; anchor>` [:ref:`string <string>`] (default: ``'mt'``) (choices: "tl", "tr", "bl", "br", "mt", "mb", "ml", "mr", "c") Origin of the text. Can be one of tl, tr, bl, br (corners), mt, mb, ml, mr
   (middle of sides), c (center). The anchors refer to the panel outline.

.. _PanelizeText_height:

-  ``height`` :index:`: <pair: output - panelize - options - configs - text4; height>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``1.5``) Height of the characters (the same parameters as KiCAD uses).

.. _PanelizeText_hjustify:

-  ``hjustify`` :index:`: <pair: output - panelize - options - configs - text4; hjustify>` [:ref:`string <string>`] (default: ``'center'``) (choices: "left", "right", "center") Horizontal justification of the text.

.. _PanelizeText_hoffset:

-  ``hoffset`` :index:`: <pair: output - panelize - options - configs - text4; hoffset>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the horizontal offset from anchor. Respects KiCAD coordinate system.

.. _PanelizeText_layer:

-  ``layer`` :index:`: <pair: output - panelize - options - configs - text4; layer>` [:ref:`string <string>`] (default: ``'F.SilkS'``) Specify text layer.

.. _PanelizeText_orientation:

-  ``orientation`` :index:`: <pair: output - panelize - options - configs - text4; orientation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the orientation (angle).

.. _PanelizeText_plugin:

-  ``plugin`` :index:`: <pair: output - panelize - options - configs - text4; plugin>` [:ref:`string <string>`] (default: ``''``) Specify the plugin that provides extra variables for the text.

.. _PanelizeText_thickness:

-  ``thickness`` :index:`: <pair: output - panelize - options - configs - text4; thickness>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.3``) Stroke thickness.

.. _PanelizeText_vjustify:

-  ``vjustify`` :index:`: <pair: output - panelize - options - configs - text4; vjustify>` [:ref:`string <string>`] (default: ``'center'``) (choices: "top", "bottom", "center") Vertical justification of the text.

.. _PanelizeText_voffset:

-  ``voffset`` :index:`: <pair: output - panelize - options - configs - text4; voffset>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the vertical offset from anchor. Respects KiCAD coordinate system.

.. _PanelizeText_width:

-  ``width`` :index:`: <pair: output - panelize - options - configs - text4; width>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``1.5``) Width of the characters (the same parameters as KiCAD uses).

