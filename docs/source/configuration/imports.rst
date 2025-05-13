.. index::
   single: import
   single: include


Import (include) from other config file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the :ref:`import-from-another` you can find how to import *outputs* from other configuration files.

The :ref:`import-other-stuff` explains how to import *preflights*, *filters*, *variants*, *global*
options and output *groups*.

The imported files can be parameterized for better reuse, consult :ref:`definitions-during-import`.

Furthermore, KiBot has some handful templates that you can import, explained in :ref:`import-templates`.


.. index::
   pair: import; outputs
   pair: include; outputs

.. _import-from-another:

Importing outputs from another file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases you may want to reuse configuration files. An example of
this are the example files that generate gerbers and drill files for
various manufacturers
(`see <https://github.com/INTI-CMNB/KiBot/tree/master/docs/samples>`__).

In this case you can create a section named ``import`` containing a list
of configuration files. Here is an example:

.. code:: yaml

   import:
     - configs/Elecrow.kibot.yaml
     - configs/FusionPCB.kibot.yaml
     - configs/JLCPCB.kibot.yaml
     - configs/P-Ban.kibot.yaml
     - configs/PCBWay.kibot.yaml

This will import all the outputs from the listed files.


.. index::
   pair: import; anything
   pair: include; anything

.. _import-other-stuff:

Importing other stuff from another file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a more complex case of the previous `Importing outputs from
another file :ref:`import-from-another`. In this case you
must use the more general syntax:

.. code:: yaml

   import:
     - file: FILE_CONTAINING_THE_YAML_DEFINITIONS
       outputs: LIST_OF_OUTPUTS
       preflights: LIST_OF_PREFLIGHTS
       filters: LIST_OF_FILTERS
       variants: LIST_OF_VARIANTS
       global: LIST_OF_GLOBALS
       groups: LIST_OF_GROUPS

This syntax is flexible. If you don’t define which ``outputs``,
``preflights``, ``filters``, ``variants``, ``global`` and/or ``groups``
all will be imported. So you can just omit them, like this:

.. code:: yaml

   import:
     - file: FILE_CONTAINING_THE_YAML_DEFINITIONS

The ``LIST_OF_items`` can be a YAML list or just one string. Here is an
example:

.. code:: yaml

   import:
     - file: FILE_CONTAINING_THE_YAML_DEFINITIONS
       outputs: one_name
       filters: ['name1', 'name2']

This will import the ``one_name`` output and the ``name1`` and ``name2``
filters. As ``variants`` is omitted, all variants will be imported. The
same applies to other things like globals and groups. You can also use
the ``all`` and ``none`` special names, like this:

.. code:: yaml

   import:
     - file: FILE_CONTAINING_THE_YAML_DEFINITIONS
       outputs: all
       filters: all
       variants: none
       global: none

.. index::
   pair: import; globals priority
   single: imported_global_has_less_priority

This will import all outputs and filters, but not variants or globals.
Also note that imported globals has more precedence than the ones
defined in the same file. If you want to give more priority to the local
values use:

.. code:: yaml

   kibot:
     version: 1
     imported_global_has_less_priority: true

   import:
   ...

Another important detail is that global options that are lists gets the
values merged. The last set of values found is inserted at the beginning
of the list. You can collect filters for all the imported global
sections.

Imports are processed recursively: An ``import`` section in an imported
file is also processed (so importing ``A.yaml`` that imports ``B.yaml``
effectively imports both).

If an import filename is a relative path, it is resolved relative to the
config file that contains the import (so it works regardless of the
working directory and, in case of recursive imports, of where top-level
config lives).

It’s recommended to always use some file extension in the
*FILE_CONTAINING_THE_YAML_DEFINITIONS* name. If you don’t use any file
extension and you use a relative path this name could be confused with
an internal template. See `Importing internal
templates :ref:`import-templates`. If you need to use a name
without any extension and a relative path, and this name is the same
used for a KiBot template use the ``is_external`` option:

.. code:: yaml

   import:
     - file: Elecrow
       is_external: true


.. index::
   pair: import; parameters
   pair: include; parameters

Parameterizable imports
^^^^^^^^^^^^^^^^^^^^^^^

You can create imports that are parametrizable. For this you must use
the mechanism explained in the :ref:`yaml-substitution` section.


.. index::
   pair: import; internal templates
   pair: include; internal templates

.. _import-templates:

Importing internal templates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

KiBot has some internally defined outputs, groups and filters. You can
easily use them with the import mechanism. Use the ``file``
mechanism and don’t include the extension for the file. When importing
an internal template you don’t need to specify its location. Here is an
example:

.. code:: yaml

   import:
     - file: Elecrow

This will import the definitions for the internal Elecrow configuration.
Note that most templates can be customized using parameters, for more
information consult the :ref:`templates-parameters` section.

Here is a list of currently defined templates and their outputs / groups:

-  **3DRender_top**: Creates a top view render using Blender. The PCB is rotated to show it better.

   - **_blender_3d_top**: Generates a PNG rotating (30, 0, -20) degrees the PCB.

-  **3DRender_top_straight**: Creates a top view render using Blender.

   - **_blender_3d_top_straight**: Generates a PNG with the stright top view.

-  **3DRender_bottom**: Creates a bottom view render using Blender. The PCB is rotated to show it better.

   - **_blender_3d_bottom**: Generates a PNG rotating (-30, 0, -20) degrees the PCB.

-  **3DRender_bottom_straight**: Creates a bottom view render using Blender.

   - **_blender_3d_bottom_straight**: Generates a PNG with the stright bottom view.

-  **CheckZoneFill**: enables the ``check_zone_fills`` preflight and checks
   the refilled PCB doesn’t changed too much.

   -  **_diff_cur_pcb_show**: Makes a diff between the PCB in memory and the one on disk
   -  **_diff_cur_pcb_check**: Computes the difference between PCB in
      memory and the one on disk. Aborts if more than 100 pixels
      changed. Use the *_KIBOT_CHKZONE_THRESHOLD* parameter to change this amount.

-  `Elecrow <https://www.elecrow.com/>`__: contain fabrication outputs
   compatible with Elecrow

   -  **_Elecrow_gerbers**: Gerbers
   -  **_Elecrow_drill**: Drill files
   -  **_Elecrow_compress**: Gerbers and drill files compressed in a ZIP
   -  **_Elecrow**: **_Elecrow_gerbers** + **_Elecrow_drill**

-  `Elecrow_stencil <https://www.elecrow.com/>`__: same as **Elecrow**,
   but also generates gerbers for *F.Paste* and *B.Paste* layers.

-  ExportProject: creates a ZIP file containing a self-contained version of the project.
   All footprint, symbols and 3D models are included.

   -  **_ExportProject**: Exports the project. Not run by default, pulled by the compress.
   -  **_ExportProject_compress**: Moves the files to a ZIP file

-  `FusionPCB <https://www.seeedstudio.io/fusion.html>`__: contain
   fabrication outputs compatible with FusionPCB

   -  **_FusionPCB_gerbers**: Gerbers
   -  **_FusionPCB_drill**: Drill files
   -  **_FusionPCB_compress**: Gerbers and drill files compressed in a ZIP
   -  **_FusionPCB**: **_FusionPCB_gerbers** + **_FusionPCB_drill**

-  `FusionPCB_stencil <https://www.seeedstudio.io/fusion.html>`__: same
   as **FusionPCB**, but also generates gerbers for *F.Paste* and *B.Paste*
   layers.

-  `JLCPCB <https://jlcpcb.com/>`__: contain fabrication outputs
   compatible with JLC PCB. Only SMD components.

   -  **_JLCPCB_gerbers**: Gerbers.
   -  **_JLCPCB_drill**: Drill files
   -  **_JLCPCB_position**: Pick and place, applies the ``_rot_footprint``
      filter. You can change this filter using the *_KIBOT_POS_PRE_TRANSFORM*
      parameter.
   -  **_JLCPCB_bom**: List of LCSC parts. Use the ``field_lcsc_part`` global
      option to specify the LCSC part number field if KiBot fails to detect it.
   -  **_JLCPCB_compress**: Gerbers, drill, position and BoM files compressed in a ZIP
   -  **_JLCPCB_fab**: **_JLCPCB_gerbers** + **_JLCPCB_drill**
   -  **_JLCPCB_assembly**: **_JLCPCB_position** + **_JLCPCB_bom**
   -  **_JLCPCB**: **_JLCPCB_fab** + **_JLCPCB_assembly**

-  `JLCPCB_stencil <https://jlcpcb.com/>`__: same as **JLCPCB**, but
   also generates gerbers for *F.Paste* and *B.Paste* layers.

-  `JLCPCB_with_THT <https://jlcpcb.com/>`__: same as **JLCPCB**, but
   also including THT components.

-  `JLCPCB_stencil_with_THT <https://jlcpcb.com/>`__: same as
   **JLCPCB_stencil**, but also including THT components.

-  `MacroFab_XYRS <https://help.macrofab.com/knowledge/macrofab-required-design-files>`__:
   XYRS position file in MacroFab format

   -  **_macrofab_xyrs**: Position file in XYRS format compatible with MacroFab.

-  PanelDemo_4x4: creates a 4x4 panel of the board, showing some of the panelize options

   -  **_PanelDemo_4x4**: The panel

-  `P-Ban <https://www.p-ban.com/>`__: contain fabrication outputs
   compatible with P-Ban

   -  **_P-Ban_gerbers**: Gerbers. You need to define the layers for more than 8 (**_KIBOT_GERBER_LAYERS** parameter).
   -  **_P-Ban_drill**: Drill files
   -  **_P-Ban**: **_P-Ban_gerbers** + **_P-Ban_drill**

-  `P-Ban_stencil <https://www.p-ban.com/>`__: same as **P-Ban**, but
   also generates gerbers for *F.Paste* and *B.Paste* layers.

-  `PCB2Blender_2_1 <https://github.com/30350n/pcb2blender>`__: Exports the PCB in a format that can be imported by the
   pcb2blender tool v2.1 or newer.

   -  **_PCB2Blender_layers_2_1**: The layers in SVG format. Disabled by default.
   -  **_PCB2Blender_vrml_2_1**: The VRML for the board. Disabled by default.
   -  **_PCB2Blender_tools_2_1**: Pads and bounds information. Disabled by default.
   -  **_PCB2Blender_2_1**: The PCB3D file. Is enabled and creates the other files.
   -  **_PCB2Blender_elements_2_1**: **_PCB2Blender_tools_2_1** + **_PCB2Blender_layers_2_1** + **_PCB2Blender_vrml_2_1**

-  `PCB2Blender_2_7 <https://github.com/30350n/pcb2blender>`__: Similar to **PCB2Blender_2_1**, but for v2.7 or newer.
   The content is the same, just using *2_7* instead of *2_1*

-  `PCB2Blender_2_17 <https://github.com/30350n/pcb2blender>`__: Similar to **PCB2Blender_2_7**, but for v2.17 or newer.
   The content is the same, just using *2_17* instead of *2_7*

-  `PCB2Blender_2_1_haschtl <https://github.com/haschtl/pcb2blender>`__: Similar to **PCB2Blender_2_1**, but for the
   experimental **haschtl** fork.

   -  Imports **PCB2Blender_2_1** and disables **_PCB2Blender_2_1**
   -  **_PCB2Blender_tools_2_1_haschtl**: Pads, bounds and stack-up information. Disabled by default.
   -  **_PCB2Blender_2_1_haschtl**: The PCB3D file. Is enabled and creates the other files.
   -  **_PCB2Blender_elements_2_1_haschtl**: **_PCB2Blender_tools_2_1_haschtl** + **_PCB2Blender_layers_2_1** + **_PCB2Blender_vrml_2_1**

-  `PCBWay <https://www.pcbway.com>`__: contain fabrication outputs compatible with PCBWay

   -  **_PCBWay_gerbers**: Gerbers
   -  **_PCBWay_drill**: Drill files
   -  **_PCBWay_compress**: Gerbers and drill files compressed in a ZIP
   -  **_PCBWay**: **_PCBWay_gerbers** + **_PCBWay_drill**

-  `PCBWay_stencil <https://www.pcbway.com>`__: same as **PCBWay**, but
   also generates gerbers for *F.Paste* and *B.Paste* layers.

-  **Testpoints_by_attr**: Creates a testpoints report in XLSX format. All pads with the testpoint fabrication attribute will be reported.

   - **_testpoints_attr**: The testpoint report

-  **Testpoints_by_attr_csv**: Creates a testpoints report in CSV format. All pads with the testpoint fabrication attribute will be reported.

   - **_testpoints_attr_csv**: The testpoint report

-  **Testpoints_by_attr_html**: Creates a testpoints report in HTML format. All pads with the testpoint fabrication attribute will be reported.

   - **_testpoints_attr_html**: The testpoint report

-  **Testpoints_by_value**: Creates a testpoints report in XLSX format. All components with value starting with *TestPoint* will be reported.

   - **_testpoints_value**: The testpoint report

-  **Testpoints_by_value_csv**: Creates a testpoints report in CSV format. All components with value starting with *TestPoint* will be reported.

   - **_testpoints_value_csv**: The testpoint report

-  **Testpoints_by_value_html**: Creates a testpoints report in HTML format. All components with value starting with *TestPoint* will be reported.

   - **_testpoints_value_html**: The testpoint report



.. _templates-parameters:

Internal templates parameters
+++++++++++++++++++++++++++++

The internal templates makes use of the :ref:`definitions during import <definitions-during-import>` mechanism to achieve
some degree of customization.

The manufacturer templates (Elecrow, FusionPCB, JLCPCB, P-Ban and PCBWay) support:

-  **_KIBOT_F_PASTE**: Layer for the front paste mask (default: '')
-  **_KIBOT_B_PASTE**: Layer for the back paste mask (default: '')
-  **_KIBOT_IMPORT_ID**: Suffix used for all outputs and groups. This can be used to import the same template more than
   once, which is useful when using different parameters (default: '')
-  **_KIBOT_IMPORT_DIR**: Target directory for the outputs (default: depends on the manufacturer)
-  **_KIBOT_MANF_DIR**: Target directory for the manufacturer outputs (default: **_KIBOT_IMPORT_DIR**)
-  **_KIBOT_MANF_DIR_COMP**: Target directory for the compressed manufacturer outputs (default: **_KIBOT_IMPORT_DIR**)
-  **_KIBOT_GERBER_LAYERS**: List of layers to use for the gerbers (default: a specially crafted list of layers)
-  **_KIBOT_PLOT_FOOTPRINT_REFS**: Include the footprint references in the gerbers (default: true)
-  **_KIBOT_PLOT_FOOTPRINT_VALUES**: Include the footprint values in the gerbers (default: true, except for JLCPCB)
-  **_KIBOT_COMPRESS_MOVE**: Move the generated files to the compressed archive (default: true)
-  **_KIBOT_DRILL_AUX_ORIGIN**: Use the auxiliar origin as coordinates origin for drill, position and gerber files (default: false, except for FusionPCB)


The JLCPCB case is a little bit more complex and also supports:

-  **_KIBOT_POS_PRE_TRANSFORM**: Name of the filer used for pretransform, needed to rotate components (default: _rot_footprint)
-  **_KIBOT_POS_ENABLED**: Generate position files (default: true)
-  **_KIBOT_BOM_ENABLED**: Generate BoM (default: true)
-  **_KIBOT_POS_ONLY_SMD**: Use only SMD components for the position files (default: true)
-  **_KIBOT_POS_DNF_FILTER**: Filter used to exclude components from the position file (default: _remove_extra). It currently
   excludes components used by KiKit to create panels.


MacroFab_XYRS:

-  **_KIBOT_MPN_FIELD**: Manufacturer field definition (default: '- field: MPN')
-  **_KIBOT_IMPORT_ID**: Suffix used for all outputs and groups (default: '')
-  **_KIBOT_IMPORT_DIR**: Target directory for the outputs (default: '.')


CheckZoneFill:

- **_KIBOT_CHKZONE_THRESHOLD**: Maximum pixels difference (default: 100)


3DRender: Is the base for **3DRender_top**, **3DRender_top_straight**, **3DRender_bottom** and **3DRender_bottom_straight**

-  **_KIBOT_IMPORT_ID**: Suffix used for the output (default: '')
-  **_KIBOT_IMPORT_DIR**: Target directory for the output (default: 'Render_3D')
-  **_KIBOT_3D_VIEW**: View point (default: 'top')
-  **_KIBOT_3D_FILE_ID**: Text used to differentiate this view from others (default: **_KIBOT_IMPORT_ID**)
-  **_KIBOT_ROT_X**: X axis rotation (default: 0)
-  **_KIBOT_ROT_Y**: Y axis rotation (default: 0)
-  **_KIBOT_ROT_Z**: Z axis rotation (default: 0)

ExportProject:

-  **_KIBOT_IMPORT_ID**: Suffix used for the output (default: '')
-  **_KIBOT_IMPORT_DIR**: Target directory for the output (default: 'ExportedProject')
-  **_KIBOT_DIR_COMP**: Target directory for the compressed ZIP (default: **_KIBOT_IMPORT_DIR**)
-  **_KIBOT_COMPRESS_MOVE**: Move the generated files to the compressed archive (default: true)

Note that manufacturer templates named *\*_stencil* are created using parameters.
As an example: *Elecrow_stencil* is just *Elecrow* customized like this:

Tespoint reports:

-  **_KIBOT_IMPORT_ID**: Suffix used for the output (default: '', but used for the CSV and HTML versions)
-  **_KIBOT_IMPORT_DIR**: Target directory for the output (default: 'Testpoints')
-  **_KIBOT_TESTPOINTS_FORMAT**: Format for the report, the default is 'XLSX', the CSV and HTML templates defines it accordingly.
-  **_KIBOT_PRE_TRANSFORM**: Pre-transform filter. The default always includes *_kicost_rename*. In the attribute version it also includes
   a filter named *_separate_pins_for_tp* used to filter the pads with testpoint attribute.
-  **_KIBOT_DNF_FILTER**: The filter used to mark things as Do Not Fit. The default is '_null'. We include the DNF components.
-  **_KIBOT_EXCLUDE_FILTER**: The filter used to exclude components. In the attributes version this filter is `_null` and in the values
   version is a filter named *_separate_testpoints* that matches components with a value starting with *TestPoint*.


.. code:: yaml

   import:
     - file: Elecrow
       definitions:
         _KIBOT_F_PASTE: '- F.Paste'
         _KIBOT_B_PASTE: '- B.Paste'
