.. _PDFUniteOptions:

:orphan:


PDFUniteOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _PDFUniteOptions_output:

-  **output** :index:`: <pair: output - pdfunite - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated PDF (%i=name of the output %x=pdf). Affected by global options.

.. _PDFUniteOptions_outputs:

-  **outputs** :index:`: <pair: output - pdfunite - options; outputs>`  [:ref:`FilesListPDFUnite parameters <FilesListPDFUnite>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Which files will be included.

.. _PDFUniteOptions_use_external_command:

-  ``use_external_command`` :index:`: <pair: output - pdfunite - options; use_external_command>` [:ref:`boolean <boolean>`] (default: ``false``) Use the `pdfunite` tool instead of PyPDF2 Python module.

Used dicts
----------

- :ref:`FilesListPDFUnite parameters <FilesListPDFUnite>`
