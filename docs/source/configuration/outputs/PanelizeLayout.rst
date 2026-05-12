.. _PanelizeLayout:

:orphan:


PanelizeLayout parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

-  **cols** :index:`: <pair: output - panelize - options - configs - layout; cols>` [:ref:`number <number>`] (default: ``1``) Specify the number of columns of boards in the grid pattern.
-  **rows** :index:`: <pair: output - panelize - options - configs - layout; rows>` [:ref:`number <number>`] (default: ``1``) Specify the number of rows of boards in the grid pattern.
-  ``alternation`` :index:`: <pair: output - panelize - options - configs - layout; alternation>` [:ref:`string <string>`] (default: ``'none'``) (choices: "none", "rows", "cols", "rowsCols") Specify alternations of board rotation.
   none: Do not alternate. |br|
   rows: Rotate boards by 180° on every next row. |br|
   cols: Rotate boards by 180° on every next column. |br|
   rowsCols: Rotate boards by 180° based on a chessboard pattern.
-  ``arg`` :index:`: <pair: output - panelize - options - configs - layout; arg>` [:ref:`string <string>`] (default: ``''``) Argument to pass to the plugin. Used for *plugin*.
-  *bake_text* :index:`: <pair: output - panelize - options - configs - layout; bake_text>` Alias for baketext.
-  ``baketext`` :index:`: <pair: output - panelize - options - configs - layout; baketext>` [:ref:`boolean <boolean>`] (default: ``true``) A flag that indicates if text variables should be substituted or not.
-  ``code`` :index:`: <pair: output - panelize - options - configs - layout; code>` [:ref:`string <string>`] (default: ``''``) Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin*.
-  *h_back_bone* :index:`: <pair: output - panelize - options - configs - layout; h_back_bone>` Alias for hbackbone.
-  *h_bone_cut* :index:`: <pair: output - panelize - options - configs - layout; h_bone_cut>` Alias for hbonecut.
-  *h_bone_first* :index:`: <pair: output - panelize - options - configs - layout; h_bone_first>` Alias for hbonefirst.
-  *h_bone_skip* :index:`: <pair: output - panelize - options - configs - layout; h_bone_skip>` Alias for hboneskip.
-  ``hbackbone`` :index:`: <pair: output - panelize - options - configs - layout; hbackbone>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) The width of horizontal backbone (0 means no backbone). The backbone does not increase the
   spacing of the boards.
-  ``hbonecut`` :index:`: <pair: output - panelize - options - configs - layout; hbonecut>` [:ref:`boolean <boolean>`] (default: ``true``) If there are both backbones specified, specifies if there should be a horizontal cut where the backbones
   cross.
-  ``hbonefirst`` :index:`: <pair: output - panelize - options - configs - layout; hbonefirst>` [:ref:`number <number>`] (default: ``0``) Specify first horizontal backbone to render.
-  ``hboneskip`` :index:`: <pair: output - panelize - options - configs - layout; hboneskip>` [:ref:`number <number>`] (default: ``0``) Skip every n horizontal backbones. I.e., 1 means place only every other backbone.
-  ``hspace`` :index:`: <pair: output - panelize - options - configs - layout; hspace>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the horizontal gap between the boards.
-  *rename_net* :index:`: <pair: output - panelize - options - configs - layout; rename_net>` Alias for renamenet.
-  *rename_ref* :index:`: <pair: output - panelize - options - configs - layout; rename_ref>` Alias for renameref.
-  ``renamenet`` :index:`: <pair: output - panelize - options - configs - layout; renamenet>` [:ref:`string <string>`] (default: ``'Board_{n}-{orig}'``) A pattern by which to rename the nets. You can use {n} and {orig} to get the board number and original name.
-  ``renameref`` :index:`: <pair: output - panelize - options - configs - layout; renameref>` [:ref:`string <string>`] (default: ``'{orig}'``) A pattern by which to rename the references. You can use {n} and {orig} to get the board number and original
   name.
-  ``rotation`` :index:`: <pair: output - panelize - options - configs - layout; rotation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Rotate the boards before placing them in the panel.
-  ``space`` :index:`: <pair: output - panelize - options - configs - layout; space>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the gap between the boards, overwrites `hspace` and `vspace`.
-  **type** :index:`: <pair: output - panelize - options - configs - layout; type>` ''
-  *v_back_bone* :index:`: <pair: output - panelize - options - configs - layout; v_back_bone>` Alias for vbackbone.
-  *v_bone_cut* :index:`: <pair: output - panelize - options - configs - layout; v_bone_cut>` Alias for vbonecut.
-  *v_bone_first* :index:`: <pair: output - panelize - options - configs - layout; v_bone_first>` Alias for vbonefirst.
-  *v_bone_skip* :index:`: <pair: output - panelize - options - configs - layout; v_bone_skip>` Alias for vboneskip.
-  ``vbackbone`` :index:`: <pair: output - panelize - options - configs - layout; vbackbone>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) The width of vertical backbone (0 means no backbone). The backbone does not increase the
   spacing of the boards.
-  ``vbonecut`` :index:`: <pair: output - panelize - options - configs - layout; vbonecut>` [:ref:`boolean <boolean>`] (default: ``true``) If there are both backbones specified, specifies if there should be a vertical cut where the backbones
   cross.
-  ``vbonefirst`` :index:`: <pair: output - panelize - options - configs - layout; vbonefirst>` [:ref:`number <number>`] (default: ``0``) Specify first vertical backbone to render.
-  ``vboneskip`` :index:`: <pair: output - panelize - options - configs - layout; vboneskip>` [:ref:`number <number>`] (default: ``0``) Skip every n vertical backbones. I.e., 1 means place only every other backbone.
-  ``vspace`` :index:`: <pair: output - panelize - options - configs - layout; vspace>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the vertical gap between the boards.

