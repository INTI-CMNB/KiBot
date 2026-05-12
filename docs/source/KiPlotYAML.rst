.. _kiplot-yaml:

KiPlot YAML
===========

You can find a lot of information about YAML format on internet. This
document doesn’t pretend to be a complete YAML reference, just a
complement to understand how to use it for the configuration files.

YAML files are structured data arranged in a way that’s easy to
understand.

The basic idea
--------------

You associate data with labels. After a label you put a colon (**:**)
and then the data:

.. code:: yaml

   version: 1

Here so associate the label **version** with the data value **1**.

Basic data types
----------------

We use three basic data types:

-  **number**: can be integer, floating point, positive and negative.
-  **boolean**: can take only two values *true* and *false*.
-  **string**: almost anything else.

.. _number:

Here are some examples for numbers:

.. code:: yaml

   v1: 1
   v2: 5.3
   v3: -3

Note that the decimal point is always a point, no matters what your
locale settings indicate.

.. _boolean:

Here are some examples for booleans:

.. code:: yaml

   v1: true
   v2: false

.. warning::
   The YAML implementation currently used by KiBot also interprets `yes`,
   `Yes`, `YES`, `on`, `On` and `ON` as *true* and `no`, `No`, `NO`,
   `off`, `Off` and `OFF` as *false*. Use 'yes' and 'no' (with quotes)
   to get an string.

.. _string:

And here are some examples for strings:

.. code:: yaml

   v1: Hi!
   v2: '3'
   v3: "true"
   v4: "  I have spaces  "
   v5: '# I have special chars'

Note that quotes are optional and can be used to disambiguate.

.. _no_case:

Also note that most strings are case sensitive, but things like schematic field names aren't.
In this case using *value* or *Value* is the same.

Compound data types
-------------------

We use two types:

-  **list**: just a list of data elements. Each element start with a
   hyphen (**-**).
-  **dict**: dictionaries or maps. Just a bunch of label with associated
   data.

.. _list(string):

Here is an example for a list of strings (**list(string)** in our case):

.. code:: yaml

   - abc
   - '3'
   - "true"
   - "  I have spaces  "

.. _dict:

And here an example for a dict:

.. code:: yaml

   v1: Hi!
   v2: '3'
   v3: "true"
   v4: "  I have spaces  "

Here the dict is mapping "Hi!" to the "v1" key, "3" to the "v2" key, etc.

The list and dict elements can also be other lists and/or dicts. To
understand how this is achieved we need one more thing.

Indentation
-----------

YAML uses the indentation to group data that belongs to a label.

Here is an example of a list associated to a label:

.. code:: yaml

   people:
     - John
     - Cindy
     - Luca
     - Laura

We use two spaces, other values are possible, but you must keep
coherence in the indentation. And here we have a dict:

.. code:: yaml

   John:
     age: 25
     gender: male

And here is a mix of both:

.. code:: yaml

   people:
     - John:
         age: 25
         gender: male
     - Cindy
     - Luca
     - Laura

The indentation shows that ``age`` and ``gender`` are attached to
``John``, not directly applied to ``people``.

.. _list(list(string)):

Note that lists can be nested, here is a list of lists
(**list(list(string))**):

.. code:: yaml

   list_of_lists:
     - - a
       - b
       - c
     - - 1
       - 2
       - 3
       - 4

In this example we have a list with two elements, the first is a list
with three elements and the second a list with four elements.

.. _list(dict):

Here is an example of a list of dicts (**list(dict)**):

.. code:: yaml

   list_of_lists:
     - name: John
       age: 25
       gender: male
     - name: Cindy
       age: 32
       gender: female


Compact notation
----------------

You can use a more compat notation for small lists and dicts. The
following list:

.. code:: yaml

   list_of_lists:
     - - a
       - b
       - c
     - - 1
       - 2
       - 3
       - 4

Can be defined in the following way:

.. code:: yaml

   list_of_lists:
     - [ a, b, c ]
     - [ 1, 2, 3, 4 ]

And this example:

.. code:: yaml

   people:
     - John:
         age: 25
         gender: male
     - Cindy
     - Luca
     - Laura

Can be defined as:

.. code:: yaml

   people:
     - John: { age: 25, gender: male }
     - Cindy
     - Luca
     - Laura

.. _comma_sep:

Also note that some options supports comma separated strings. This is common
for options that can be a single string, or a list of strings. In this case
the following are equivalent:

.. code:: yaml

   people: John,Cindy,Luca,Laura

And:

.. code:: yaml

   people:
     - John
     - Cindy
     - Luca
     - Laura


Putting all together
--------------------

So a **.kiplot.yaml** file is basically a dict containing the following
labels:

-  ``kiplot``: contains a dict with special global options. Currently
   the format version used.
-  ``preflight``: contains a dict with pre-flight (or pre-run) actions.
-  ``outputs``: contains a list of outputs (or targets).

Advanced tricks
---------------

If you have various similar outputs with repeating options you can use
*anchors*. This a nice YAML feature that allows to memorize a value and
reuse it.

Here is an example:

.. code:: yaml

   kiplot:
     version: 1

   outputs:
     - name: PcbDraw 1
       comment: "PcbDraw test top"
       type: pcbdraw
       dir: PcbDraw
       options: &pcb_draw_ops
         format: svg
         style:
           board: "#1b1f44"
           copper: "#00406a"
           silk: "#d5dce4"
           pads: "#cfb96e"
           clad: "#72786c"
           outline: "#000000"
           vcut: "#bf2600"
           highlight_on_top: false
           highlight_style: "stroke:none;fill:#ff0000;opacity:0.5;"
           highlight_padding: 1.5
         libs:
           - default
           - eagle-default
         remap:
           L_G1: "LEDs:LED-5MM_green"
           L_B1: "LEDs:LED-5MM_blue"
           L_Y1: "LEDs:LED-5MM_yellow"
           PHOTO1: "yaqwsx:R_PHOTO_7mm"
           J8: "yaqwsx:Pin_Header_Straight_1x02_circle"
           'REF**': "dummy:dummy"
           G***: "dummy:dummy"
           svg2mod: "dummy:dummy"
           JP1: "dummy:dummy"
           JP2: "dummy:dummy"
           JP3: "dummy:dummy"
           JP4: "dummy:dummy"
         no_drillholes: False
         mirror: False
         highlight:
           - L_G1
           - L_B1
           - R10
           - RV1
         show_components: all
         vcuts: True
         warnings: visible
         dpi: 600

     - name: PcbDraw 2
       comment: "PcbDraw test bottom"
       type: pcbdraw
       dir: PcbDraw
       options:
         <<: *pcb_draw_ops
         style: set-red-enig
         bottom: True
         show_components:
           - L_G1
           - L_B1
         remap:

Here we have two outputs: ‘PcbDraw 1’ and ‘PcbDraw 2’. The options for
are big because we are including a custom color style and a list of
component remappings. In this case ‘PcbDraw 2’ wants to use the same
options, but with some changes. So we use an anchor in the first options
list (``&pcb_draw_ops``) and then we copy the data with
``<<: *pcb_draw_ops``. The good thing is that we can overwrite options.
Here we choose another ``style`` (ridiculous example), the bottom side
(good example), a different list of components to show and we eliminate
the ``remap`` dict.


KiBot specific data types
-------------------------

KiBot defines some data types that are derived from YAML basic data types.

.. _string_dict:

string_dict
...........

This is a :ref:`dict <dict>` with the restriction that all the values must be strings.
The following example is a valid `string_dict`:

.. code:: yaml

   v1: Hi!
   v2: '3'
   v3: "true"
   v4: "  I have spaces  "

But the following isn't:

.. code:: yaml

   v1: Hi!
   v2: 3
   v3: "true"
   v4: "  I have spaces  "

This is because we assign a number to the `v2` key, not a string.
String dicts are used to define pairs of strings.


.. _list(string_dict):

list(string_dict)
.................

This is just a list of :ref:`string_dict <string_dict>`

.. code:: yaml

   - v1: Hi!
     v2: '3'
   - v1: Bye!
     v2: '4'

Here you have two elements, each element is a :ref:`string_dict <string_dict>`.
