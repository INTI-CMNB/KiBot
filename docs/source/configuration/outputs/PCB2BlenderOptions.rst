.. _PCB2BlenderOptions:

:orphan:


PCB2BlenderOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``center`` :index:`: <pair: output - blender_export - options - pcb_import; center>` [:ref:`boolean <boolean>`] (default: ``true``) Center the PCB at the coordinates origin.
-  ``components`` :index:`: <pair: output - blender_export - options - pcb_import; components>` [:ref:`boolean <boolean>`] (default: ``true``) Import the components.
-  ``cut_boards`` :index:`: <pair: output - blender_export - options - pcb_import; cut_boards>` [:ref:`boolean <boolean>`] (default: ``true``) Separate the sub-PCBs in separated 3D models.
-  ``enhance_materials`` :index:`: <pair: output - blender_export - options - pcb_import; enhance_materials>` [:ref:`boolean <boolean>`] (default: ``true``) Create good looking materials.
-  ``merge_materials`` :index:`: <pair: output - blender_export - options - pcb_import; merge_materials>` [:ref:`boolean <boolean>`] (default: ``true``) Reuse materials.
-  ``solder_joints`` :index:`: <pair: output - blender_export - options - pcb_import; solder_joints>` [:ref:`string <string>`] (default: ``'SMART'``) (choices: "NONE", "SMART", "ALL") The plug-in can add nice looking solder joints.
   This option controls if we add it for none, all or only for THT/SMD pads with solder paste.
-  ``stack_boards`` :index:`: <pair: output - blender_export - options - pcb_import; stack_boards>` [:ref:`boolean <boolean>`] (default: ``true``) Move the sub-PCBs to their relative position.
-  ``texture_dpi`` :index:`: <pair: output - blender_export - options - pcb_import; texture_dpi>` [:ref:`number <number>`] (default: ``1016.0``) (range: 508 to 2032) Texture density in dots per inch.

