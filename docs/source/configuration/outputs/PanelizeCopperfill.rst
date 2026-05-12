.. _PanelizeCopperfill:

:orphan:


PanelizeCopperfill parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **type** :index:`: <pair: output - panelize - options - configs - copperfill; type>` ''
-  ``clearance`` :index:`: <pair: output - panelize - options - configs - copperfill; clearance>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.5``) Extra clearance from the board perimeters. Suitable for, e.g., not filling the tabs with
   copper.
-  ``diameter`` :index:`: <pair: output - panelize - options - configs - copperfill; diameter>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``7``) Diameter of hexagons.
-  *edge_clearance* :index:`: <pair: output - panelize - options - configs - copperfill; edge_clearance>` Alias for edgeclearance.
-  ``edgeclearance`` :index:`: <pair: output - panelize - options - configs - copperfill; edgeclearance>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0.5``) Specifies clearance between the fill and panel perimeter.
-  ``layers`` :index:`: <pair: output - panelize - options - configs - copperfill; layers>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'F.Cu,B.Cu'``) [:ref:`comma separated <comma_sep>`] List of layers to fill. Can be a comma-separated string.
   Using *all* means all external copper layers.

-  ``orientation`` :index:`: <pair: output - panelize - options - configs - copperfill; orientation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``45``) The orientation of the hatched strokes.
-  ``spacing`` :index:`: <pair: output - panelize - options - configs - copperfill; spacing>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``1``) The space between the hatched strokes or hexagons.
-  ``threshold`` :index:`: <pair: output - panelize - options - configs - copperfill; threshold>` [:ref:`number <number>`] (default: ``15``) Remove fragments smaller than threshold. Expressed as a percentage.
-  ``width`` :index:`: <pair: output - panelize - options - configs - copperfill; width>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``1``) The width of the hatched strokes.

