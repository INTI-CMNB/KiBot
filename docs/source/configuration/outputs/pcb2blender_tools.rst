.. Automatically generated by KiBot, please don't edit this file

.. index::
   pair: PCB2Blender Tools; pcb2blender_tools

PCB2Blender Tools
~~~~~~~~~~~~~~~~~

A bunch of tools used to generate PCB3D files used to export PCBs to Blender.
Blender is the most important free software 3D render package. |br|
This output needs KiCad 6 or newer. |br|
The PCB3D file format is used by the PCB2Blender project (https://github.com/30350n/pcb2blender)
to import KiCad PCBs in Blender. |br|
You need to install a Blender plug-in to load PCB3D files. |br|
The tools in this output are used by internal templates used to generate PCB3D files. |br|

Type: ``pcb2blender_tools``

Category: **PCB/3D/Auxiliar**

Parameters:

-  **comment** :index:`: <pair: output - pcb2blender_tools; comment>` [:ref:`string <string>`] (default: ``''``) A comment for documentation purposes. It helps to identify the output.
-  **dir** :index:`: <pair: output - pcb2blender_tools; dir>` [:ref:`string <string>`] (default: ``'./'``) Output directory for the generated files.
   If it starts with `+` the rest is concatenated to the default dir.
-  **name** :index:`: <pair: output - pcb2blender_tools; name>` [:ref:`string <string>`] (default: ``''``) Used to identify this particular output definition.
   Avoid using `_` as first character. These names are reserved for KiBot.
-  **options** :index:`: <pair: output - pcb2blender_tools; options>`  [:ref:`PCB2Blender_ToolsOptions parameters <PCB2Blender_ToolsOptions>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options for the `pcb2blender_tools` output.
-  **type** :index:`: <pair: output - pcb2blender_tools; type>` 'pcb2blender_tools'
-  ``category`` :index:`: <pair: output - pcb2blender_tools; category>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] The category for this output. If not specified an internally defined
   category is used. |br|
   Categories looks like file system paths, i.e. **PCB/fabrication/gerber**. |br|
   Using '.' or './' as a category puts the file at the root. |br|
   The categories are currently used for `navigate_results` and `navigate_results_rb`.

-  ``disable_run_by_default`` :index:`: <pair: output - pcb2blender_tools; disable_run_by_default>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) Use it to disable the `run_by_default` status of other output.
   Useful when this output extends another and you don't want to generate the original. |br|
   Use the boolean true value to disable the output you are extending.
-  ``extends`` :index:`: <pair: output - pcb2blender_tools; extends>` [:ref:`string <string>`] (default: ``''``) Copy the `options` section from the indicated output.
   Used to inherit options from another output of the same type.
-  ``groups`` :index:`: <pair: output - pcb2blender_tools; groups>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) One or more groups to add this output. In order to catch typos
   we recommend to add outputs only to existing groups. You can create an empty group if
   needed.

-  ``output_id`` :index:`: <pair: output - pcb2blender_tools; output_id>` [:ref:`string <string>`] (default: ``''``) Text to use for the %I expansion content. To differentiate variations of this output.
-  ``priority`` :index:`: <pair: output - pcb2blender_tools; priority>` [:ref:`number <number>`] (default: ``50``) (range: 0 to 100) Priority for this output. High priority outputs are created first.
   Internally we use 10 for low priority, 90 for high priority and 50 for most outputs.
-  ``run_by_default`` :index:`: <pair: output - pcb2blender_tools; run_by_default>` [:ref:`boolean <boolean>`] (default: ``true``) When enabled this output will be created when no specific outputs are requested.

.. toctree::
   :caption: Used dicts

   PCB2Blender_ToolsOptions
