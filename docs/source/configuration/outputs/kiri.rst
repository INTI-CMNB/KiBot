.. Automatically generated by KiBot, please don't edit this file

.. index::
   pair: KiRi; kiri

KiRi
~~~~

Generates an interactive web page to browse the schematic and/or PCB differences between git commits.
Must be applied to a git repository. |br|
Recursive git submodules aren't supported (submodules inside submodules). |br|
Note that most browsers won't allow Java Script to read local files,
needed to load the SCH/PCB. So you must use a web server or enable the
access to local files. In the case of Google Chrome you can use the
`--allow-file-access-from-files` command line option. |br|
This output generates a simple Python web server called `kiri-server` that you can use. |br|
For more information visit the `KiRi web <https://github.com/leoheck/kiri>`__

Type: ``kiri``

Categories: **PCB/docs**, **Schematic/docs**

Parameters:

-  **comment** :index:`: <pair: output - kiri; comment>` [:ref:`string <string>`] (default: ``''``) A comment for documentation purposes. It helps to identify the output.
-  **dir** :index:`: <pair: output - kiri; dir>` [:ref:`string <string>`] (default: ``'./'``) Output directory for the generated files.
   If it starts with `+` the rest is concatenated to the default dir.
-  **layers** :index:`: <pair: output - kiri; layers>`  [:ref:`Layer parameters <Layer>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>` | :ref:`string <string>`] (default: ``'all'``) (choices: "all", "selected", "copper", "technical", "user", "inners", "outers") (also accepts any string) List
   of PCB layers to use. When empty all available layers are used. |br|
   Note that if you want to support adding/removing layers you should specify a list here.
-  **name** :index:`: <pair: output - kiri; name>` [:ref:`string <string>`] (default: ``''``) Used to identify this particular output definition.
   Avoid using `_` as first character. These names are reserved for KiBot.
-  **options** :index:`: <pair: output - kiri; options>`  [:ref:`KiRiOptions parameters <KiRiOptions>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options for the `diff` output.
-  **type** :index:`: <pair: output - kiri; type>` 'kiri'
-  ``category`` :index:`: <pair: output - kiri; category>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] The category for this output. If not specified an internally defined
   category is used. |br|
   Categories looks like file system paths, i.e. **PCB/fabrication/gerber**. |br|
   Using '.' or './' as a category puts the file at the root. |br|
   The categories are currently used for `navigate_results` and `navigate_results_rb`.

-  ``disable_run_by_default`` :index:`: <pair: output - kiri; disable_run_by_default>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) Use it to disable the `run_by_default` status of other output.
   Useful when this output extends another and you don't want to generate the original. |br|
   Use the boolean true value to disable the output you are extending.
-  ``extends`` :index:`: <pair: output - kiri; extends>` [:ref:`string <string>`] (default: ``''``) Copy the `options` section from the indicated output.
   Used to inherit options from another output of the same type.
-  ``groups`` :index:`: <pair: output - kiri; groups>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) One or more groups to add this output. In order to catch typos
   we recommend to add outputs only to existing groups. You can create an empty group if
   needed.

-  ``output_id`` :index:`: <pair: output - kiri; output_id>` [:ref:`string <string>`] (default: ``''``) Text to use for the %I expansion content. To differentiate variations of this output.
-  ``priority`` :index:`: <pair: output - kiri; priority>` [:ref:`number <number>`] (default: ``50``) (range: 0 to 100) Priority for this output. High priority outputs are created first.
   Internally we use 10 for low priority, 90 for high priority and 50 for most outputs.
-  ``run_by_default`` :index:`: <pair: output - kiri; run_by_default>` [:ref:`boolean <boolean>`] (default: ``true``) When enabled this output will be created when no specific outputs are requested.

.. toctree::
   :caption: Used dicts

   KiRiOptions
   Layer
