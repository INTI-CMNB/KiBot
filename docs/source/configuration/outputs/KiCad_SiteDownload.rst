.. _KiCad_SiteDownload:

:orphan:


KiCad_SiteDownload parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **name** :index:`: <pair: output - kicad_site - options - downloads; name>` [:ref:`string <string>`] (default: ``''``) Name for the downloadable item.
-  ``dir`` :index:`: <pair: output - kicad_site - options - downloads; dir>` [:ref:`string <string>`] (default: ``''``) Internal directory to store it, leave empty to use the same as the output that generates it.
-  ``index`` :index:`: <pair: output - kicad_site - options - downloads; index>` [:ref:`number <number>`] (default: ``0``) Used when the output generates more than one file.
   Here you can select which one, 0 is the first. |br|
   Note that negative indexes are counted from the end of the list. |br|
   Using an out of range value will generate an error and show all available files.
-  ``output`` :index:`: <pair: output - kicad_site - options - downloads; output>` [:ref:`string <string>`] (default: ``''``) Output that generates it.

