.. index::
   single: preflights

The *preflight* section
~~~~~~~~~~~~~~~~~~~~~~~

This section is used to specify tasks that will be executed before
generating any output.


.. index::
   pair: supported; preflights

.. include:: sup_preflights.rst

Here is an example of a *preflight* section:

.. code:: yaml

   preflight:
     erc: true
     drc: true
     check_zone_fills: true

If you define the same preflight more than once the last definition is used.
Some preflights takes a list of options, in this case you might want to merge
multiple definitions, from various files. To achieve this use the `merge_pre`
option in the `kibot` section, provide a list of the preflight types that
will be merged. See the :ref:`header section <header>`.

.. note::
   The `merge_pre` option must be in the top-level configuration file and
   is used for all the imported files.


.. index::
   pair: preflights; pcb_replace
   pair: preflights; sch_replace

More about *pcb_replace* and *sch_replace*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These options are supposed to be used in a version control environment.
This is because, unlike other options, they modify the PCB and/or
schematic and might damage them. In a version control environment you
can just roll-back the changes.

Don’t be afraid, they make a back-up of the files and also tries to
disable dangerous changes. But should be used carefully. They are ideal
for CI/CD environment where you don’t actually commit any changes.


.. index::
   pair: filters; DRC and ERC errors

.. _filter-drc-and-erc:

Filtering DRC and ERC errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes KiCad reports DRC or ERC errors that you can’t get rid off.
This could be just because you are part of a team including lazy people
that doesn’t want to take the extra effort to solve some errors that
aren’t in fact errors, just small violations made on purpose. In this
case you could exclude some known errors.

KiCad 5 didn't have a mechanism to exclude errors. KiCad 6 introduced
exclusion, but they failed to be honred when using the Python API.
Starting with KiCad 8 you can use KiCad exclusions, but in some cases
they fail, this is because they are very specific. KiBot filters are
more generic and can solve cases where KiCad exclusions aren't enough.

For this you must declare ``filters`` entry in the ``drc`` and/or ``erc``
sections. Then you can add as many ``filter`` entries as you want. Each
filter entry has an optional description and defines to which error type
is applied (``error``) and a regular expression that the error must
match to be ignored (``regex``). Like this:

.. code:: yaml

     filters:
       - filter: 'Optional filter description'
         error: 'Error_type'
         regex:  'Expression to match'

Here is a KiCad 5 example, suppose you are getting the following errors:

::

   ** Found 1 DRC errors **
   ErrType(4): Track too close to pad
       @(177.185 mm, 78.315 mm): Track 1.000 mm [Net-(C3-Pad1)] on F.Cu, length: 1.591 mm
       @(177.185 mm, 80.715 mm): Pad 2 of C3 on F.Cu and others

   ** Found 1 unconnected pads **
   ErrType(2): Unconnected items
       @(177.185 mm, 73.965 mm): Pad 2 of C4 on F.Cu and others
       @(177.185 mm, 80.715 mm): Pad 2 of C3 on F.Cu and others

And you want to ignore them. You can add the following filters:

.. code:: yaml

     filters:
       - filter: 'Ignore C3 pad 2 too close to anything'
         error: '4'
         regex:  'Pad 2 of C3'
       - filter: 'Ignore unconnected pad 2 of C4'
         error: '2'
         regex:  'Pad 2 of C4'

If you need to match text from two different lines in the error message
try using ``(?s)TEXT(.*)TEXT_IN_OTHER_LINE``.

If you have two or more different options for a text to match try using
``(OPTION1|OPTION2)``.

A complete Python regular expressions explanation is out of the scope of
this manual. For a complete reference consult the `Python
manual <https://docs.python.org/3/library/re.html>`__.

KiCad 6 uses strings to differentiate errors, use them for the ``error``
field. To keep compatibility you can use the ``number`` or
``error_number`` options for KiCad 5.

Note that this will ignore the errors, but they will be reported as
warnings. If you want to suppress these warnings take a look at
:ref:`filter-kibot-warnings`

.. note::
   The old ``run_drc`` and ``run_erc`` preflights used a
   separated ``filters`` preflight. Avoid using it with the new ``drc`` and
   ``erc`` preflights, they have its own ``filters`` option.

.. note::
   When using the old ``run_drc`` and ``run_erc``
   preflights the ``filters`` preflight will create a file named
   *kibot_errors.filter* in the output directory.
