.. Automatically generated by KiBot, please don't edit this file

.. index::
   pair: Set Text Variables; set_text_variables

Set Text Variables
~~~~~~~~~~~~~~~~~~

Defines KiCad 6+ variables.
They are expanded using `${VARIABLE}`, and stored in the project file. |br|
This preflight replaces `pcb_replace` and `sch_replace` when using KiCad 6 or newer. |br|
The KiCad project file is modified. |br|

.. warning::
       don't use `-s all` or this preflight will be skipped
.. 

   -  **set_text_variables** :index:`: <pair: preflight - set_text_variables; set_text_variables>`  [:ref:`KiCadVariable parameters <KiCadVariable_pre>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: ``[]``) One or more variable definition.

.. toctree::
   :caption: Used dicts

   KiCadVariable
