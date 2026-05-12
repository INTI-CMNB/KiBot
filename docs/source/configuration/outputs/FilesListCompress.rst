.. _FilesListCompress:

:orphan:


FilesListCompress parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **from_output** :index:`: <pair: output - compress - options - files; from_output>` [:ref:`string <string>`] (default: ``''``) Collect files from the selected output.
   When used the `source` option is ignored.
-  **source** :index:`: <pair: output - compress - options - files; source>` [:ref:`string <string>`] (default: ``'*'``) File names to add, wildcards allowed. Use ** for recursive match.
   By default this pattern is applied to the output dir specified with `-d` command line option. |br|
   See the `from_cwd` and `from_output_dir` options.
-  ``dest`` :index:`: <pair: output - compress - options - files; dest>` [:ref:`string <string>`] (default: ``''``) Destination directory inside the archive, empty means the same of the file.
-  ``filter`` :index:`: <pair: output - compress - options - files; filter>` [:ref:`string <string>`] (default: ``'.*'``) A regular expression that source files must match.
-  ``from_cwd`` :index:`: <pair: output - compress - options - files; from_cwd>` [:ref:`boolean <boolean>`] (default: ``false``) Use the current working directory instead of the dir specified by `-d`.
-  ``from_output_dir`` :index:`: <pair: output - compress - options - files; from_output_dir>` [:ref:`boolean <boolean>`] (default: ``false``) Use the current directory specified by the output instead of the dir specified by `-d`.
   Note that it only applies when using `from_output` and no `dest` is specified. |br|
   It has more prescedence than `from_cwd`.

