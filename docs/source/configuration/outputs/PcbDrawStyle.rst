.. _PcbDrawStyle:

:orphan:


PcbDrawStyle parameters
~~~~~~~~~~~~~~~~~~~~~~~

-  **board** :index:`: <pair: output - pcbdraw - options - style; board>` [:ref:`string <string>`] (default: ``'#208b47'``) Color for the board without copper (covered by solder mask).
-  **clad** :index:`: <pair: output - pcbdraw - options - style; clad>` [:ref:`string <string>`] (default: ``'#cabb3e'``) Color for the PCB core (not covered by solder mask).
-  **copper** :index:`: <pair: output - pcbdraw - options - style; copper>` [:ref:`string <string>`] (default: ``'#285e3a'``) Color for the copper zones (covered by solder mask).
-  **outline** :index:`: <pair: output - pcbdraw - options - style; outline>` [:ref:`string <string>`] (default: ``'#000000'``) Color for the outline.
-  **pads** :index:`: <pair: output - pcbdraw - options - style; pads>` [:ref:`string <string>`] (default: ``'#8b898c'``) Color for the exposed pads (metal finish).
-  **silk** :index:`: <pair: output - pcbdraw - options - style; silk>` [:ref:`string <string>`] (default: ``'#d5dce4'``) Color for the silk screen.
-  ``highlight_on_top`` :index:`: <pair: output - pcbdraw - options - style; highlight_on_top>` [:ref:`boolean <boolean>`] (default: ``false``) Highlight over the component (not under).
-  ``highlight_padding`` :index:`: <pair: output - pcbdraw - options - style; highlight_padding>` [:ref:`number <number>`] (default: ``1.5``) (range: 0 to 1000) How much the highlight extends around the component [mm].
-  ``highlight_style`` :index:`: <pair: output - pcbdraw - options - style; highlight_style>` [:ref:`string <string>`] (default: ``'stroke:none;fill:#ff0000;opacity:0.5;'``) SVG code for the highlight style.
-  ``vcut`` :index:`: <pair: output - pcbdraw - options - style; vcut>` [:ref:`string <string>`] (default: ``'#bf2600'``) Color for the V-CUTS.

