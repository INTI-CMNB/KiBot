.. _KiKit_PresentOptions:

:orphan:


KiKit_PresentOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **description** :index:`: <pair: output - kikit_present - options; description>` [:ref:`string <string>`] (default: ``''``) Name for a markdown file containing the main part of the page to be generated.
   This is mandatory and is the description of your project. |br|
   You can embed the markdown code. If the text doesn't map to a file and contains
   more than one line KiBot will assume this is the markdown. |br|
   If empty KiBot will generate a silly text and a warning.
-  ``boards`` :index:`: <pair: output - kikit_present - options; boards>`  [:ref:`PresentBoards parameters <PresentBoards>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: list with one empty dict, default values used) One or more boards that compose your project.
   When empty we will use only the main PCB for the current project.
-  ``name`` :index:`: <pair: output - kikit_present - options; name>` [:ref:`string <string>`] (default: ``''``) Name of the project. Will be passed to the template.
   If empty we use the name of the KiCad project. |br|
   The default template uses it for things like the page title.
-  ``repository`` :index:`: <pair: output - kikit_present - options; repository>` [:ref:`string <string>`] (default: ``''``) URL of the repository. Will be passed to the template.
   If empty we will try to find it using `git remote get-url origin`. |br|
   The default template uses it to create an URL for the current commit.
-  ``resources`` :index:`: <pair: output - kikit_present - options; resources>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``)  A list of file name patterns for additional resources to be included.
   I.e. images referenced in description. |br|
   They will be copied relative to the output dir.

-  ``template`` :index:`: <pair: output - kikit_present - options; template>` [:ref:`string <string>`] (default: ``'default'``) Path to a template directory or a name of built-in one.
   See KiKit's doc/present.md for template specification.

Used dicts
----------

- :ref:`PresentBoards parameters <PresentBoards>`
