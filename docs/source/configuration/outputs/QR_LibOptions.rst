.. _QR_LibOptions:

:orphan:


QR_LibOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~

-  **lib** :index:`: <pair: output - qr_lib - options; lib>` [:ref:`string <string>`] (default: ``'QR'``) Short name for the library.
-  **output** :index:`: <pair: output - qr_lib - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename/dirname for the output library (%i=qr, %x=lib/kicad_sym/pretty).
   You must use %x in the name to get a symbols lib and a footprints lib. Affected by global options.
-  **qrs** :index:`: <pair: output - qr_lib - options; qrs>`  [:ref:`QRCodeOptions parameters <QRCodeOptions>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: list with one empty dict, default values used) QR codes to include in the library.
-  ``reference`` :index:`: <pair: output - qr_lib - options; reference>` [:ref:`string <string>`] (default: ``'QR'``) The reference prefix.
-  ``use_sch_dir`` :index:`: <pair: output - qr_lib - options; use_sch_dir>` [:ref:`boolean <boolean>`] (default: ``true``) Generate the libs relative to the schematic/PCB dir.

Used dicts
----------

- :ref:`QRCodeOptions parameters <QRCodeOptions>`
