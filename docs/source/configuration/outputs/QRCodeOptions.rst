.. _QRCodeOptions:

:orphan:


QRCodeOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~

-  **layer** :index:`: <pair: output - qr_lib - options - qrs; layer>` [:ref:`string <string>`] (default: ``'silk'``) (choices: "silk", "copper") Layer for the footprint.
-  **name** :index:`: <pair: output - qr_lib - options - qrs; name>` [:ref:`string <string>`] (default: ``'QR'``) Name for the symbol/footprint.
-  **size_pcb** :index:`: <pair: output - qr_lib - options - qrs; size_pcb>` [:ref:`number <number>`] (default: ``15``) Size of the QR footprint.
-  **size_sch** :index:`: <pair: output - qr_lib - options - qrs; size_sch>` [:ref:`number <number>`] (default: ``15``) Size of the QR symbol.
-  **text** :index:`: <pair: output - qr_lib - options - qrs; text>` [:ref:`string <string>`] (default: ``'%p %r'``) Text to encode as QR.
-  ``correction_level`` :index:`: <pair: output - qr_lib - options - qrs; correction_level>` [:ref:`string <string>`] (default: ``'low'``) (choices: "low", "medium", "quartile", "high") Error correction level.
-  ``pcb_negative`` :index:`: <pair: output - qr_lib - options - qrs; pcb_negative>` [:ref:`boolean <boolean>`] (default: ``false``) Generate a negative image for the PCB.
-  ``size_units`` :index:`: <pair: output - qr_lib - options - qrs; size_units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches") Units used for the size.

