.. _header:

.. index::
   pair: configuration; header

The header
~~~~~~~~~~

All configuration files must start with:

.. code:: yaml

   kibot:
     version: 1

This tells to KiBot that this file is using version 1 of the format.


.. index::
   pair: preflight; merge
   single: merge_pre


You can specify which preflights are allowed to be merged using the
`merge_pre` option. This should be a single string or a list of strings
with the type of preflights that can be merged. This is useful when you
want to add more elements to a preflight that takes a list, i.e.
`set_text_variables`.

.. note::
   The `merge_pre` option must be in the top-level configuration file and
   is used for all the imported files.


.. note::
   You can merge all type of preflights specifying `all`


In this section you can also define the priority of imported global
options. More :ref:`here <imported-global-has-less-priority>`.
