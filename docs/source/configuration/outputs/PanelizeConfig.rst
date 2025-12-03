.. _PanelizeConfig:

:orphan:


PanelizeConfig parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

-  **cuts** :index:`: <pair: output - panelize - options - configs; cuts>`  [:ref:`PanelizeCuts parameters <PanelizeCuts>`] [:ref:`dict <dict>`] (default: ``null``) Specify how to perform the cuts on the tabs separating the board.
-  **fiducials** :index:`: <pair: output - panelize - options - configs; fiducials>`  [:ref:`PanelizeFiducials parameters <PanelizeFiducials>`] [:ref:`dict <dict>`] (default: ``null``) Used to add fiducial marks to the (rail/frame of) the panel.
-  **framing** :index:`: <pair: output - panelize - options - configs; framing>`  [:ref:`PanelizeFraming parameters <PanelizeFraming>`] [:ref:`dict <dict>`] (default: ``null``) Specify the frame around the boards.
-  **layout** :index:`: <pair: output - panelize - options - configs; layout>`  [:ref:`PanelizeLayout parameters <PanelizeLayout>`] [:ref:`dict <dict>`] (default: ``null``) Layout used for the panel.
-  **page** :index:`: <pair: output - panelize - options - configs; page>`  [:ref:`PanelizePage parameters <PanelizePage>`] [:ref:`dict <dict>`] (default: ``null``) Sets page size on the resulting panel and position the panel in the page.
-  **tabs** :index:`: <pair: output - panelize - options - configs; tabs>`  [:ref:`PanelizeTabs parameters <PanelizeTabs>`] [:ref:`dict <dict>`] (default: ``null``) Style of the tabs used to join the PCB copies.
-  **tooling** :index:`: <pair: output - panelize - options - configs; tooling>`  [:ref:`PanelizeTooling parameters <PanelizeTooling>`] [:ref:`dict <dict>`] (default: ``null``) Used to add tooling holes to the (rail/frame of) the panel.
-  ``copperfill`` :index:`: <pair: output - panelize - options - configs; copperfill>`  [:ref:`PanelizeCopperfill parameters <PanelizeCopperfill>`] [:ref:`dict <dict>`] (default: ``null``) Fill non-board areas of the panel with copper.
-  ``debug`` :index:`: <pair: output - panelize - options - configs; debug>`  [:ref:`PanelizeDebug parameters <PanelizeDebug>`] [:ref:`dict <dict>`] (default: ``null``) Debug options.
-  ``expand_text`` :index:`: <pair: output - panelize - options - configs; expand_text>` [:ref:`boolean <boolean>`] (default: ``true``) Expand text variables and KiBot %X markers in text objects.
-  ``extends`` :index:`: <pair: output - panelize - options - configs; extends>` [:ref:`string <string>`] (default: ``''``) A configuration to use as base for this one. Use the following format: `OUTPUT_NAME[CFG_NAME]`.
-  ``name`` :index:`: <pair: output - panelize - options - configs; name>` [:ref:`string <string>`] (default: ``''``) A name to identify this configuration. If empty will be the order in the list, starting with 1.
   Don't use just a number or it will be confused as an index.
-  ``post`` :index:`: <pair: output - panelize - options - configs; post>`  [:ref:`PanelizePost parameters <PanelizePost>`] [:ref:`dict <dict>`] (default: ``null``) Finishing touches to the panel.
-  ``source`` :index:`: <pair: output - panelize - options - configs; source>`  [:ref:`PanelizeSource parameters <PanelizeSource>`] [:ref:`dict <dict>`] (default: ``null``) Used to adjust details of which part of the PCB is panelized.
-  ``text`` :index:`: <pair: output - panelize - options - configs; text>`  [:ref:`PanelizeText parameters <PanelizeText>`] [:ref:`dict <dict>`] (default: ``null``) Used to add text to the panel.
-  ``text2`` :index:`: <pair: output - panelize - options - configs; text2>`  [:ref:`PanelizeText parameters <PanelizeText>`] [:ref:`dict <dict>`] (default: ``null``) Used to add text to the panel.
-  ``text3`` :index:`: <pair: output - panelize - options - configs; text3>`  [:ref:`PanelizeText parameters <PanelizeText>`] [:ref:`dict <dict>`] (default: ``null``) Used to add text to the panel.
-  ``text4`` :index:`: <pair: output - panelize - options - configs; text4>`  [:ref:`PanelizeText parameters <PanelizeText>`] [:ref:`dict <dict>`] (default: ``null``) Used to add text to the panel.

Used dicts
----------

- :ref:`PanelizeCopperfill parameters <PanelizeCopperfill>`
- :ref:`PanelizeCuts parameters <PanelizeCuts>`
- :ref:`PanelizeDebug parameters <PanelizeDebug>`
- :ref:`PanelizeFiducials parameters <PanelizeFiducials>`
- :ref:`PanelizeFraming parameters <PanelizeFraming>`
- :ref:`PanelizeLayout parameters <PanelizeLayout>`
- :ref:`PanelizePage parameters <PanelizePage>`
- :ref:`PanelizePost parameters <PanelizePost>`
- :ref:`PanelizeSource parameters <PanelizeSource>`
- :ref:`PanelizeTabs parameters <PanelizeTabs>`
- :ref:`PanelizeText parameters <PanelizeText>`
- :ref:`PanelizeTooling parameters <PanelizeTooling>`
