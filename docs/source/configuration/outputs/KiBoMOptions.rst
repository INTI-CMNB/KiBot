.. _KiBoMOptions:

:orphan:


KiBoMOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~


.. _KiBoMOptions_format:

-  **format** :index:`: <pair: output - kibom - options; format>` [:ref:`string <string>`] (default: ``'HTML'``) (choices: "HTML", "CSV", "XML", "XLSX") Format for the BoM.

.. _KiBoMOptions_number:

-  **number** :index:`: <pair: output - kibom - options; number>` [:ref:`number <number>`] (default: ``1``) Number of boards to build (components multiplier).

.. _KiBoMOptions_output:

-  **output** :index:`: <pair: output - kibom - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=bom). Affected by global options.

.. _KiBoMOptions_conf:

-  ``conf`` :index:`: <pair: output - kibom - options; conf>`  [:ref:`KiBoMConfig parameters <KiBoMConfig>`] [:ref:`string <string>` | :ref:`dict <dict>`] (default: ``'bom.ini'``) BoM configuration file, relative to PCB. Environment variables and ~ allowed.
   You can also define the configuration here, will be stored in `config.kibom.ini`.

.. _KiBoMOptions_separator:

-  ``separator`` :index:`: <pair: output - kibom - options; separator>` [:ref:`string <string>`] (default: ``','``) CSV Separator.

.. _KiBoMOptions_variant:

-  ``variant`` :index:`: <pair: output - kibom - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant(s), used to determine which components
   are output to the BoM. To specify multiple variants,
   with a BOM file exported for each variant, separate
   variants with the ';' (semicolon) character. |br|
   This isn't related to the KiBot concept of variants.

Used dicts
----------

- :ref:`KiBoMConfig parameters <KiBoMConfig>`
