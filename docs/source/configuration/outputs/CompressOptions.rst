.. _CompressOptions:

:orphan:


CompressOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _CompressOptions_files:

-  **files** :index:`: <pair: output - compress - options; files>`  [:ref:`FilesListCompress parameters <FilesListCompress>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Which files will be included.

.. _CompressOptions_format:

-  **format** :index:`: <pair: output - compress - options; format>` [:ref:`string <string>`] (default: ``'ZIP'``) (choices: "ZIP", "TAR", "RAR") Output file format.

.. _CompressOptions_output:

-  **output** :index:`: <pair: output - compress - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated archive (%i=name of the output %x=according to format). Affected by global options.

.. _CompressOptions_compression:

-  ``compression`` :index:`: <pair: output - compress - options; compression>` [:ref:`string <string>`] (default: ``'auto'``) (choices: "auto", "stored", "deflated", "bzip2", "lzma") Compression algorithm. Use auto to let KiBot select a suitable one.

.. _CompressOptions_expand_dest:

-  ``expand_dest`` :index:`: <pair: output - compress - options; expand_dest>` [:ref:`boolean <boolean>`] (default: ``true``) Also expand the `dest` file name (using % patterns).

.. _CompressOptions_follow_links:

-  ``follow_links`` :index:`: <pair: output - compress - options; follow_links>` [:ref:`boolean <boolean>`] (default: ``true``) Store the file pointed by symlinks, not the symlink.

.. _CompressOptions_move_files:

-  ``move_files`` :index:`: <pair: output - compress - options; move_files>` [:ref:`boolean <boolean>`] (default: ``false``) Move the files to the archive. In other words: remove the files after adding them to the archive.

.. _CompressOptions_remove_files:

-  *remove_files* :index:`: <pair: output - compress - options; remove_files>` Alias for move_files.

.. _CompressOptions_skip_not_run:

-  ``skip_not_run`` :index:`: <pair: output - compress - options; skip_not_run>` [:ref:`boolean <boolean>`] (default: ``false``) Skip outputs with `run_by_default: false`.

Used dicts
----------

- :ref:`FilesListCompress parameters <FilesListCompress>`
