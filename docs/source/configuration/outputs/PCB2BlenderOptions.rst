.. _PCB2BlenderOptions:

:orphan:


PCB2BlenderOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _PCB2BlenderOptions_center:

-  ``center`` :index:`: <pair: output - blender_export - options - pcb_import; center>` [:ref:`boolean <boolean>`] (default: ``true``) Center the PCB at the coordinates origin.

.. _PCB2BlenderOptions_components:

-  ``components`` :index:`: <pair: output - blender_export - options - pcb_import; components>` [:ref:`boolean <boolean>`] (default: ``true``) Import the components.

.. _PCB2BlenderOptions_cut_boards:

-  ``cut_boards`` :index:`: <pair: output - blender_export - options - pcb_import; cut_boards>` [:ref:`boolean <boolean>`] (default: ``true``) Separate the sub-PCBs in separated 3D models.

.. _PCB2BlenderOptions_enhance_materials:

-  ``enhance_materials`` :index:`: <pair: output - blender_export - options - pcb_import; enhance_materials>` [:ref:`boolean <boolean>`] (default: ``true``) Create good looking materials.

.. _PCB2BlenderOptions_merge_materials:

-  ``merge_materials`` :index:`: <pair: output - blender_export - options - pcb_import; merge_materials>` [:ref:`boolean <boolean>`] (default: ``true``) Reuse materials.

.. _PCB2BlenderOptions_solder_joints:

-  ``solder_joints`` :index:`: <pair: output - blender_export - options - pcb_import; solder_joints>` [:ref:`string <string>`] (default: ``'SMART'``) (choices: "NONE", "SMART", "ALL") The plug-in can add nice looking solder joints.
   This option controls if we add it for none, all or only for THT/SMD pads with solder paste.

.. _PCB2BlenderOptions_stack_boards:

-  ``stack_boards`` :index:`: <pair: output - blender_export - options - pcb_import; stack_boards>` [:ref:`boolean <boolean>`] (default: ``true``) Move the sub-PCBs to their relative position.

.. _PCB2BlenderOptions_texture_dpi:

-  ``texture_dpi`` :index:`: <pair: output - blender_export - options - pcb_import; texture_dpi>` [:ref:`number <number>`] (default: ``1016.0``) (range: 508 to 2032) Texture density in dots per inch.

