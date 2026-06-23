.. _FilesListPDFUnite:

:orphan:


FilesListPDFUnite parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _FilesListPDFUnite_from_output:

-  **from_output** :index:`: <pair: output - pdfunite - options - outputs; from_output>` [:ref:`string <string>`] (default: ``''``) Collect files from the selected output.
   When used the `source` option is ignored.

.. _FilesListPDFUnite_source:

-  **source** :index:`: <pair: output - pdfunite - options - outputs; source>` [:ref:`string <string>`] (default: ``'*.pdf'``) File names to add, wildcards allowed. Use ** for recursive match.
   By default this pattern is applied to the output dir specified with `-d` command line option. |br|
   See the `from_cwd` option.

.. _FilesListPDFUnite_filter:

-  ``filter`` :index:`: <pair: output - pdfunite - options - outputs; filter>` [:ref:`string <string>`] (default: ``'.*\\.pdf'``) A regular expression that source files must match.

.. _FilesListPDFUnite_from_cwd:

-  ``from_cwd`` :index:`: <pair: output - pdfunite - options - outputs; from_cwd>` [:ref:`boolean <boolean>`] (default: ``false``) Use the current working directory instead of the dir specified by `-d`.

