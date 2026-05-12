.. _PanelizeText:

:orphan:


PanelizeText parameters
~~~~~~~~~~~~~~~~~~~~~~~

-  **text** :index:`: <pair: output - panelize - options - configs - text4; text>` [:ref:`string <string>`] (default: ``''``) The text to be displayed. Note that you can escape ; via \\.
   Available variables in text: *date* formats current date as <year>-<month>-<day>,
   *time24* formats current time in 24-hour format,
   *boardTitle* the title from the source board,
   *boardDate* the date from the source board,
   *boardRevision* the revision from the source board,
   *boardCompany* the company from the source board,
   *boardComment1*-*boardComment9* comments from the source board.
-  **type** :index:`: <pair: output - panelize - options - configs - text4; type>` ''
-  ``anchor`` :index:`: <pair: output - panelize - options - configs - text4; anchor>` [:ref:`string <string>`] (default: ``'mt'``) (choices: "tl", "tr", "bl", "br", "mt", "mb", "ml", "mr", "c") Origin of the text. Can be one of tl, tr, bl, br (corners), mt, mb, ml, mr
   (middle of sides), c (center). The anchors refer to the panel outline.
-  ``height`` :index:`: <pair: output - panelize - options - configs - text4; height>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``1.5``) Height of the characters (the same parameters as KiCAD uses).
-  ``hjustify`` :index:`: <pair: output - panelize - options - configs - text4; hjustify>` [:ref:`string <string>`] (default: ``'center'``) (choices: "left", "right", "center") Horizontal justification of the text.
-  ``hoffset`` :index:`: <pair: output - panelize - options - configs - text4; hoffset>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the horizontal offset from anchor. Respects KiCAD coordinate system.
-  ``layer`` :index:`: <pair: output - panelize - options - configs - text4; layer>` [:ref:`string <string>`] (default: ``'F.SilkS'``) Specify text layer.
-  ``orientation`` :index:`: <pair: output - panelize - options - configs - text4; orientation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the orientation (angle).
-  ``plugin`` :index:`: <pair: output - panelize - options - configs - text4; plugin>` [:ref:`string <string>`] (default: ``''``) Specify the plugin that provides extra variables for the text.
-  ``thickness`` :index:`: <pair: output - panelize - options - configs - text4; thickness>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.3``) Stroke thickness.
-  ``vjustify`` :index:`: <pair: output - panelize - options - configs - text4; vjustify>` [:ref:`string <string>`] (default: ``'center'``) (choices: "top", "bottom", "center") Vertical justification of the text.
-  ``voffset`` :index:`: <pair: output - panelize - options - configs - text4; voffset>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the vertical offset from anchor. Respects KiCAD coordinate system.
-  ``width`` :index:`: <pair: output - panelize - options - configs - text4; width>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``1.5``) Width of the characters (the same parameters as KiCAD uses).

