.. _PanelizeLayout:

:orphan:


PanelizeLayout parameters
~~~~~~~~~~~~~~~~~~~~~~~~~


.. _PanelizeLayout_cols:

-  **cols** :index:`: <pair: output - panelize - options - configs - layout; cols>` [:ref:`number <number>`] (default: ``1``) Specify the number of columns of boards in the grid pattern.

.. _PanelizeLayout_rows:

-  **rows** :index:`: <pair: output - panelize - options - configs - layout; rows>` [:ref:`number <number>`] (default: ``1``) Specify the number of rows of boards in the grid pattern.

.. _PanelizeLayout_alternation:

-  ``alternation`` :index:`: <pair: output - panelize - options - configs - layout; alternation>` [:ref:`string <string>`] (default: ``'none'``) (choices: "none", "rows", "cols", "rowsCols") Specify alternations of board rotation.
   none: Do not alternate. |br|
   rows: Rotate boards by 180° on every next row. |br|
   cols: Rotate boards by 180° on every next column. |br|
   rowsCols: Rotate boards by 180° based on a chessboard pattern.

.. _PanelizeLayout_arg:

-  ``arg`` :index:`: <pair: output - panelize - options - configs - layout; arg>` [:ref:`string <string>`] (default: ``''``) Argument to pass to the plugin. Used for *plugin*.

.. _PanelizeLayout_bake_text:

-  *bake_text* :index:`: <pair: output - panelize - options - configs - layout; bake_text>` Alias for baketext.

.. _PanelizeLayout_baketext:

-  ``baketext`` :index:`: <pair: output - panelize - options - configs - layout; baketext>` [:ref:`boolean <boolean>`] (default: ``true``) A flag that indicates if text variables should be substituted or not.

.. _PanelizeLayout_code:

-  ``code`` :index:`: <pair: output - panelize - options - configs - layout; code>` [:ref:`string <string>`] (default: ``''``) Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin*.

.. _PanelizeLayout_h_back_bone:

-  *h_back_bone* :index:`: <pair: output - panelize - options - configs - layout; h_back_bone>` Alias for hbackbone.

.. _PanelizeLayout_h_bone_cut:

-  *h_bone_cut* :index:`: <pair: output - panelize - options - configs - layout; h_bone_cut>` Alias for hbonecut.

.. _PanelizeLayout_h_bone_first:

-  *h_bone_first* :index:`: <pair: output - panelize - options - configs - layout; h_bone_first>` Alias for hbonefirst.

.. _PanelizeLayout_h_bone_skip:

-  *h_bone_skip* :index:`: <pair: output - panelize - options - configs - layout; h_bone_skip>` Alias for hboneskip.

.. _PanelizeLayout_hbackbone:

-  ``hbackbone`` :index:`: <pair: output - panelize - options - configs - layout; hbackbone>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) The width of horizontal backbone (0 means no backbone). The backbone does not increase the
   spacing of the boards.

.. _PanelizeLayout_hbonecut:

-  ``hbonecut`` :index:`: <pair: output - panelize - options - configs - layout; hbonecut>` [:ref:`boolean <boolean>`] (default: ``true``) If there are both backbones specified, specifies if there should be a horizontal cut where the backbones
   cross.

.. _PanelizeLayout_hbonefirst:

-  ``hbonefirst`` :index:`: <pair: output - panelize - options - configs - layout; hbonefirst>` [:ref:`number <number>`] (default: ``0``) Specify first horizontal backbone to render.

.. _PanelizeLayout_hboneskip:

-  ``hboneskip`` :index:`: <pair: output - panelize - options - configs - layout; hboneskip>` [:ref:`number <number>`] (default: ``0``) Skip every n horizontal backbones. I.e., 1 means place only every other backbone.

.. _PanelizeLayout_hspace:

-  ``hspace`` :index:`: <pair: output - panelize - options - configs - layout; hspace>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the horizontal gap between the boards.

.. _PanelizeLayout_rename_net:

-  *rename_net* :index:`: <pair: output - panelize - options - configs - layout; rename_net>` Alias for renamenet.

.. _PanelizeLayout_rename_ref:

-  *rename_ref* :index:`: <pair: output - panelize - options - configs - layout; rename_ref>` Alias for renameref.

.. _PanelizeLayout_renamenet:

-  ``renamenet`` :index:`: <pair: output - panelize - options - configs - layout; renamenet>` [:ref:`string <string>`] (default: ``'Board_{n}-{orig}'``) A pattern by which to rename the nets. You can use {n} and {orig} to get the board number and original name.

.. _PanelizeLayout_renameref:

-  ``renameref`` :index:`: <pair: output - panelize - options - configs - layout; renameref>` [:ref:`string <string>`] (default: ``'{orig}'``) A pattern by which to rename the references. You can use {n} and {orig} to get the board number and original
   name.

.. _PanelizeLayout_rotation:

-  ``rotation`` :index:`: <pair: output - panelize - options - configs - layout; rotation>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Rotate the boards before placing them in the panel.

.. _PanelizeLayout_space:

-  ``space`` :index:`: <pair: output - panelize - options - configs - layout; space>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the gap between the boards, overwrites `hspace` and `vspace`.

.. _PanelizeLayout_type:

-  **type** :index:`: <pair: output - panelize - options - configs - layout; type>` ''

.. _PanelizeLayout_v_back_bone:

-  *v_back_bone* :index:`: <pair: output - panelize - options - configs - layout; v_back_bone>` Alias for vbackbone.

.. _PanelizeLayout_v_bone_cut:

-  *v_bone_cut* :index:`: <pair: output - panelize - options - configs - layout; v_bone_cut>` Alias for vbonecut.

.. _PanelizeLayout_v_bone_first:

-  *v_bone_first* :index:`: <pair: output - panelize - options - configs - layout; v_bone_first>` Alias for vbonefirst.

.. _PanelizeLayout_v_bone_skip:

-  *v_bone_skip* :index:`: <pair: output - panelize - options - configs - layout; v_bone_skip>` Alias for vboneskip.

.. _PanelizeLayout_vbackbone:

-  ``vbackbone`` :index:`: <pair: output - panelize - options - configs - layout; vbackbone>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) The width of vertical backbone (0 means no backbone). The backbone does not increase the
   spacing of the boards.

.. _PanelizeLayout_vbonecut:

-  ``vbonecut`` :index:`: <pair: output - panelize - options - configs - layout; vbonecut>` [:ref:`boolean <boolean>`] (default: ``true``) If there are both backbones specified, specifies if there should be a vertical cut where the backbones
   cross.

.. _PanelizeLayout_vbonefirst:

-  ``vbonefirst`` :index:`: <pair: output - panelize - options - configs - layout; vbonefirst>` [:ref:`number <number>`] (default: ``0``) Specify first vertical backbone to render.

.. _PanelizeLayout_vboneskip:

-  ``vboneskip`` :index:`: <pair: output - panelize - options - configs - layout; vboneskip>` [:ref:`number <number>`] (default: ``0``) Skip every n vertical backbones. I.e., 1 means place only every other backbone.

.. _PanelizeLayout_vspace:

-  ``vspace`` :index:`: <pair: output - panelize - options - configs - layout; vspace>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Specify the vertical gap between the boards.

