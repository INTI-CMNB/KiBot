.. index::
   pair: supported; outputs

The *outputs* section
~~~~~~~~~~~~~~~~~~~~~

In this section you put all the things that you want to generate. This
section contains one or more **outputs**. Each output contain the
following data:

-  ``name`` a name so you can easily identify it.
-  ``comment`` a short description of this output.
-  ``type`` selects which type of output will be generated. Examples are
   *gerbers*, *drill files* and *pick & place files*
-  ``dir`` is the directory where this output will be stored.
-  ``extends`` used to use another output’s ``options`` as base.
-  ``run_by_default`` indicates this output will be created when no
   specific outputs are requested.
-  ``disable_run_by_default`` can be used to disable the
   ``run_by_default`` status of other output.
-  ``output_id`` text to use for the %I expansion content.
-  ``options`` contains one or more options to configure this output.
-  ``layers`` a list of layers used for this output. Not all outputs
   needs this subsection.

**Important note about the layers**: In the original
`kiplot <https://github.com/johnbeard/kiplot>`__ (from `John
Beard <https://github.com/johnbeard>`__) the name of the inner layers
was *Inner.N* where *N* is the number of the layer, i.e. *Inner.1* is
the first inner layer. This format is supported for compatibility. Note
that this generated a lot of confusion because the default KiCad name
for the first inner layer is *In1.Cu*. People filled issues and
submitted pull-requests to fix it, thinking that inner layers weren’t
supported. Currently KiCad allows renaming these layers, so this version
of kiplot supports the name used in KiCad. Just use the same name you
see in the user interface.

The available values for *type* are:

.. index::
   pair: supported; plot formats
   pair: outputs; plot formats

-  Plot formats:

   -  ``gerber`` the gerbers for fabrication.
   -  ``ps`` postscript plot
   -  ``hpgl`` format for laser printers
   -  ``svg`` scalable vector graphics
   -  ``pdf`` portable document format
   -  ``dxf`` mechanical CAD format

.. index::
   pair: supported; drill formats
   pair: outputs; drill formats

-  Drill formats:

   -  ``excellon`` data for the drilling machine
   -  ``gerb_drill`` drilling positions in a gerber file

.. index::
   pair: supported; pick and place formats
   pair: outputs; pick and place formats

-  Pick & place

   -  ``position`` of the components for the pick & place machine

.. index::
   pair: supported; documentation formats
   pair: outputs; documentation formats

-  Documentation

   -  ``pdf_sch_print`` schematic in PDF format
   -  ``svg_sch_print`` schematic in SVG format
   -  ``ps_sch_print`` schematic in PS format
   -  ``dxf_sch_print`` schematic in DXF format
   -  ``hpgl_sch_print`` schematic in HPGL format
   -  ``pdf_pcb_print`` PDF file containing one or more layer and the
      page frame
   -  ``svg_pcb_print`` SVG file containing one or more layer and the
      page frame
   -  ``pcb_print`` PDF/SVG/PNG/EPS/PS, similar to ``pdf_pcb_print`` and
      ``svg_pcb_print``, with more flexibility
   -  ``report`` generates a report about the PDF. Can include images
      from the above outputs.
   -  ``diff`` creates PDF files showing schematic or PCB changes.
   -  ``kiri`` creates an interactive web page showing schematic or PCB changes.

.. index::
   pair: supported; Bill of Materials
   pair: outputs; Bill of Materials

-  Bill of Materials

   -  ``bom`` The internal BoM generator.
   -  ``kibom`` BoM in HTML or CSV format generated by
      `KiBoM <https://github.com/INTI-CMNB/KiBoM>`__
   -  ``ibom`` Interactive HTML BoM generated by
      `InteractiveHtmlBom <https://github.com/INTI-CMNB/InteractiveHtmlBom>`__
   -  ``kicost`` BoM in XLSX format with costs generated by
      `KiCost <https://github.com/INTI-CMNB/KiCost>`__

.. index::
   pair: supported; 3D model formats
   pair: outputs; 3D model formats
   pair: supported; 3D render
   pair: outputs; 3D render

-  3D model:

   -  ``step`` *Standard for the Exchange of Product Data* for the PCB
   -  ``vrml`` *Virtual Reality Modeling Language* for the PCB
   -  ``render_3d`` PCB render, from the KiCad’s 3D Viewer
   -  ``blender_export`` PCB export to Blender and high quality 3D
      render. Including export to: ``fbx`` (Kaydara’s Filmbox), ‘obj’
      (Wavefront), ‘x3d’ (ISO/IEC standard), ``gltf`` (GL format),
      ``stl`` (3D printing) and ‘ply’ (Stanford).

.. index::
   pair: supported; web page generation
   pair: outputs; web page generation

-  Web pages:

   -  ``populate`` To create step-by-step assembly instructions.
   -  ``kikit_present`` To create a project presentation web page.
   -  ``navigate_results`` generates web pages to navigate the generated
      outputs.
   - ``kicanvas`` creates a web page to display the schematic and/or PCB

.. index::
   pair: supported; fabrication helpers
   pair: outputs; fabrication helpers

-  Fabrication helpers:

   -  ``panelize`` creates a PCB panel containing N copies of the PCB.
   -  ``stencil_3d`` creates a 3D self-registering printable stencil.
   -  ``stencil_for_jig`` creates steel stencils and 3D register.

.. index::
   pair: supported; other stuff
   pair: outputs; other stuff

-  Others:

   -  ``boardview`` creates a file useful to repair the board, but
      without disclosing the full layout.
   -  ``gencad`` exports the PCB in GENCAD format.
   -  ``compress`` creates an archive containing generated data.
   -  ``download_datasheets`` downloads the datasheets for all the
      components.
   -  ``pcbdraw`` nice images of the PCB in customized colors.
   -  ``pdfunite`` joins various PDF files into one.
   -  ``qr_lib`` generates symbol and footprints for QR codes.
   -  ``sch_variant`` the schematic after applying all filters and
      variants, including crossed components.
   -  ``pcb_variant`` the PCB after applying all filters and variants,
      including modified 3D models.
   -  ``copy_files`` used to copy generated files and source material.
   -  ``info`` creates a report about the tools used during the KiBot
      run.
   -  ``netlist`` generates the list of connections for the project
      (classic and IPC-D-356 formats).

Here is an example of a configuration file to generate the gerbers for
the top and bottom layers:

.. index::
   pair: example; gerber

.. code:: yaml

   kibot:
     version: 1

   preflight:
     run_drc: true

   outputs:

     - name: 'gerbers'
       comment: "Gerbers for the board house"
       type: gerber
       dir: gerberdir
       options:
         # generic layer options
         exclude_edge_layer: false
         exclude_pads_from_silkscreen: false
         plot_sheet_reference: false
         plot_footprint_refs: true
         plot_footprint_values: true
         force_plot_invisible_refs_vals: false
         tent_vias: true
         line_width: 0.15

         # gerber options
         use_aux_axis_as_origin: false
         subtract_mask_from_silk: true
         use_protel_extensions: false
         gerber_precision: 4.5
         create_gerber_job_file: true
         use_gerber_x2_attributes: true
         use_gerber_net_attributes: false

       layers:
         - 'F.Cu'
         - 'B.Cu'

Most options are the same you’ll find in the KiCad dialogs.

Outputs are generated in the order they are declared in the YAML file.
To create them in an arbitrary order use the ``--cli-order`` command
line option and they will be created in the order specified in the
command line.


.. index::
   pair: configuration; PCB layers
   pair: outputs; PCB layers

Specifying the layers
^^^^^^^^^^^^^^^^^^^^^

You have various ways to specify the layers. If you need to specify just
one layer you can just use its name:

.. code:: yaml

       layers: 'F.Cu'

If you want to specify all the available layers:

.. code:: yaml

       layers: 'all'

You can also select the layers you want in KiCad (using File, Plot
dialog) and save your PCB. Then you just need to use:

.. code:: yaml

       layers: 'selected'

You can also use any of the following grup of layers:

-  **copper** all the copper layers
-  **technical** all the technical layers (silk sreen, solder mask,
   paste, adhesive, etc.)
-  **user** all the user layers (draw, comments, eco, margin, edge cuts,
   etc.)
-  **inners** all the inner copper layers
-  **outers** all the outer copper layers

You can also mix the above definitions using a list:

.. code:: yaml

       layers:
         - 'copper'
         - 'Dwgs.User'

This will select all the copper layers and the user drawings. Note that
the above mentioned options will use file name suffixes and descriptions
selected automatically. If you want to use a particular suffix and
provide better descriptions you can use the following format:

.. code:: yaml

       layers:
         - layer: 'F.Cu'
           suffix: 'F_Cu'
           description: 'Front copper'
         - layer: 'B.Cu'
           suffix: 'B_Cu'
           description: 'Bottom copper'

You can also mix the styles:

.. code:: yaml

       layers:
         - 'copper'
         - layer: 'Cmts.User'
           suffix: 'Cmts_User'
           description: 'User comments'
         - 'Dwgs.User'

If you need to use the same list of layers for various outputs you can
use YAML anchors. The first time you define the list of layers just
assign an anchor, here is an example:

.. code:: yaml

       layers: &copper_and_cmts
         - copper
         - 'Cmts.User'

Next time you need this list just use an alias, like this:

.. code:: yaml

       layers: *copper_and_cmts


.. index::
   pair: configuration; all outputs

.. include:: sup_outputs.rst

.. index::
   pair: Bill of Materials; consolidate
   pair: Bill of Materials; merge
   pair: Bill of Materials; aggregate

Consolidating BoMs
^^^^^^^^^^^^^^^^^^

Some times your project is composed by various boards, other times you
are producing various products at the same time. In both cases you would
want to consolidate the components acquisition in one operation. Of
course you can create individual BoMs for each project in CSV format and
then consolidate them using a spreadsheet editor. But KiBot offers
another option: you create a BoM for your main project and then
aggregate the components from the other projects.

Here is a simple example. Suppose you have three projects: *merge_1*,
*merge_2* and *merge_3*. For the *merge_1* project you could use the
following output:

.. code:: yaml

   kibot:
     version: 1

   outputs:
     - name: 'bom_csv'
       comment: "Bill of Materials in CSV format"
       type: bom
       dir: BoM
       options:
         use_alt: true

Using the ``tests/board_samples/kicad_5/merge_1.sch`` from the git repo
and storing the above example in ``m1.kibot.yaml`` you could run:

.. code:: shell

   src/kibot -c m1.kibot.yaml -e tests/board_samples/kicad_5/merge_1.sch -d test_merge

And get ``test_merge/BoM/merge_1-bom.csv``:

+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| Row      | Description      | Part | References | Value | Footprint | Quantity | Status | Datasheet |
|          |                  |      |            |       |           | Per PCB  |        |           |
+==========+==================+======+============+=======+===========+==========+========+===========+
| 1        | Unpolarized      | C    | C1         | 1nF   |           | 1        |        | ~         |
|          | capacitor        |      |            |       |           |          |        |           |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| 2        | Unpolarized      | C    | C2         | 10nF  |           | 1        |        | ~         |
|          | capacitor        |      |            |       |           |          |        |           |
|          |                  |      |            |       |           |          |        |           |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| 3        | Resistor         | R    | R1-R3      | 1k    |           | 3        |        | ~         |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+

================== =================================
Project info:      
================== =================================
Schematic:         merge_1
Variant:           default
Revision:          
Date:              2021-02-02_12-12-27
KiCad Version:     5.1.9-73d0e3b20d~88~ubuntu21.04.1
Statistics:        
Component Groups:  3
Component Count:   5
Fitted Components: 5
Number of PCBs:    1
Total Components:  5
================== =================================

This CSV says you have five components groped in three different types.
They are one 1 nF capacitor, one 10 nF capacitor and three 1 k
resistors. Now lets generate BoMs for the *merge_2* example:

.. code:: shell

   src/kibot -c m1.kibot.yaml -e tests/board_samples/kicad_5/merge_2.sch -d test_merge

We’ll get ``test_merge/BoM/merge_2-bom.csv``:

+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| Row      | Description      | Part | References | Value | Footprint | Quantity | Status | Datasheet |
|          |                  |      |            |       |           | Per PCB  |        |           |
+==========+==================+======+============+=======+===========+==========+========+===========+
| 1        | Unpolarized      | C    | C2         | 1nF   |           | 1        |        | ~         |
|          | capacitor        |      |            |       |           |          |        |           |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| 2        | Unpolarized      | C    | C1         | 10nF  |           | 1        |        | ~         |
|          | capacitor        |      |            |       |           |          |        |           |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| 3        | Resistor         | R    | R2-R4      | 1000  |           | 3        |        | ~         |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| 4        | Resistor         | R    | R1         | 10k   |           | 1        |        | ~         |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+

================== =================================
Project info:      
================== =================================
Schematic:         merge_2
Variant:           default
Revision:          
Date:              2021-01-27_10-19-46
KiCad Version:     5.1.9-73d0e3b20d~88~ubuntu21.04.1
Statistics:        
Component Groups:  4
Component Count:   6
Fitted Components: 6
Number of PCBs:    1
Total Components:  6
================== =================================

In this project we have six components from four different types. They
are similar to *merge_1* but now we also have a 10 k resistor. We don’t
need to generate this BoM to consolidate our projects, but is good to
know what we have. And now lets generate BoMs for the *merge_3* example:

.. code:: shell

   src/kibot -c m1.kibot.yaml -e tests/board_samples/kicad_5/merge_3.sch -d test_merge

We’ll get ``test_merge/BoM/merge_3-bom.csv``:

+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| Row      | Description      | Part | References | Value | Footprint | Quantity | Status | Datasheet |
|          |                  |      |            |       |           | Per PCB  |        |           |
+==========+==================+======+============+=======+===========+==========+========+===========+
| 1        | Resistor         | R    | R5         | 1k    |           | 1        |        | ~         |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+
| 2        | Resistor         | R    | R1-R4      | 10k   |           | 4        |        | ~         |
+----------+------------------+------+------------+-------+-----------+----------+--------+-----------+

================== =================================
Project info:      
================== =================================
Schematic:         merge_3
Variant:           default
Revision:          
Date:              2021-01-27_10-21-29
KiCad Version:     5.1.9-73d0e3b20d~88~ubuntu21.04.1
Statistics:        
Component Groups:  2
Component Count:   5
Fitted Components: 5
Number of PCBs:    1
Total Components:  5
================== =================================

This time we also have five components, but from two different types.
They are one 1 k resistor and four 10 k resistors. Now suppose we want
to create 10 boards for *merge_1*, 20 for *merge_2* and 30 for
*merge_3*. We could use the following configuration:

.. code:: yaml

   kibot:
     version: 1

   outputs:
     - name: 'bom_csv'
       comment: "Bill of Materials in CSV format"
       type: bom
       dir: BoM
       options:
         use_alt: true
         number: 10
         aggregate:
           - file: tests/board_samples/kicad_5/merge_2.sch
             number: 20
           - file: tests/board_samples/kicad_5/merge_3.sch
             number: 30

Save it as ``m2.kibot.yaml`` and run:

.. code:: shell

   src/kibot -c m2.kibot.yaml -e tests/board_samples/kicad_5/merge_1.sch -d test_merge_consolidate

The ``test_merge_consolidate/BoM/merge_1-bom.csv`` file will be
generated containing:

+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| Row      | Description      | Part | References | Value | Footprint | Quantity | Build    | Status | Datasheet | Source BoM |
|          |                  |      |            |       |           | Per PCB  | quantity |        |           |            |
+==========+==================+======+============+=======+===========+==========+==========+========+===========+============+
| 1        | Unpolarized      | C    | C1 C2      | 1nF   |           | 2        | 30       |        | ~         | merge_1(1) |
|          | capacitor        |      |            |       |           |          |          |        |           | merge_2(1) |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 2        | Unpolarized      | C    | C2 C1      | 10nF  |           | 2        | 30       |        | ~         | merge_1(1) |
|          | capacitor        |      |            |       |           |          |          |        |           | merge_2(1) |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 3        | Resistor         | R    | R1-R3      | 1k    |           | 7        | 120      |        | ~         | merge_1(3) |
|          |                  |      | R2-R4      |       |           |          |          |        |           | merge_2(3) |
|          |                  |      | R5         |       |           |          |          |        |           | merge_3(1) |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 4        | Resistor         | R    | R1 R1-R4   | 10k   |           | 5        | 140      |        | ~         | merge_2(1) |
|          |                  |      |            |       |           |          |          |        |           | merge_3(4) |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+

================== =================================
Project info:      
================== =================================
Variant:           default
KiCad Version:     5.1.9-73d0e3b20d~88~ubuntu21.04.1
Global statistics: 
Component Groups:  4
Component Count:   16
Fitted Components: 16
Number of PCBs:    60
Total Components:  320
Project info:      merge_1
Schematic:         merge_1
Revision:          
Date:              2021-02-02_12-12-27
Company:           Test company
Statistics:        merge_1
Component Groups:  3
Component Count:   5
Fitted Components: 5
Number of PCBs:    10
Total Components:  50
Project info:      merge_2
Schematic:         merge_2
Revision:          
Date:              2021-01-27_10-19-46
Statistics:        merge_2
Component Groups:  4
Component Count:   6
Fitted Components: 6
Number of PCBs:    20
Total Components:  120
Project info:      merge_3
Schematic:         merge_3
Revision:          
Date:              2021-01-27_10-21-29
Statistics:        merge_3
Component Groups:  2
Component Count:   5
Fitted Components: 5
Number of PCBs:    30
Total Components:  150
================== =================================

You can see that now we have much more stats. They say we have four
different types, thirteen for board sets, a total of 60 boards and 250
components. Then we have individual stats for each project. The
capacitors are easy to interpret, we have 30 1 nF capacitors *merge_1*
project has one and *merge_2* another. As we have 10 *merge_1* and 20
*merge_2* boards this is clear. But looking at the 1 k resistors is
harder. We have 80, three from *merge_1*, one from *merge_2* and another
from *merge_3*. So we have 10\ *3+20*\ 3+30=120, this is clear, but the
BoM says they are R1-R3 R2-R4 R5, which is a little bit confusing. In
this simple example is easy to correlate R1-R3 to *merge_1*, R2-R4 to
*merge_2* and R5 to *merge_1*. For bigger projects this gets harder.
Lets assign an *id* to each project, we’ll use ‘A’ for *merge_1*, ‘B’
for *merge_2* and ‘C’ for *merge_3*:

.. code:: yaml

   kibot:
     version: 1

   outputs:
     - name: 'bom_csv'
       comment: "Bill of Materials in CSV format"
       type: bom
       dir: BoM
       options:
         use_alt: true
         number: 10
         ref_id: 'A:'
         aggregate:
           - file: tests/board_samples/kicad_5/merge_2.sch
             number: 20
             ref_id: 'B:'
           - file: tests/board_samples/kicad_5/merge_3.sch
             number: 30
             ref_id: 'C:'

Now ``test_merge_consolidate/BoM/merge_1-bom.csv`` will have the
following information:

+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| Row      | Description      | Part | References | Value | Footprint | Quantity | Build    | Status | Datasheet | Source BoM |
|          |                  |      |            |       |           | Per PCB  | quantity |        |           |            |
+==========+==================+======+============+=======+===========+==========+==========+========+===========+============+
| 1        | Unpolarized      | C    | A:C1 B:C2  | 1nF   |           | 2        | 30       |        | ~         | merge_1(1) |
|          | capacitor        |      |            |       |           |          |          |        |           | merge_2(1) |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 2        | Unpolarized      | C    | A:C2 B:C1  | 10nF  |           | 2        | 30       |        | ~         | merge_1(1) |
|          | capacitor        |      |            |       |           |          |          |        |           | merge_2(1) |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 3        | Resistor         | R    | A:R1-A:R3  | 1k    |           | 7        | 120      |        | ~         | merge_1(3) |
|          |                  |      | B:R2-B:R4  |       |           |          |          |        |           | merge_2(3) |
|          |                  |      | C:R5       |       |           |          |          |        |           | merge_3(1) |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 4        | Resistor         | R    | B:R1       | 10k   |           | 5        | 140      |        | ~         | merge_2(1) |
|          |                  |      | C:R1-C:R4  |       |           |          |          |        |           | merge_3(4) |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+

As you can see now we know ``A`` has R1-R3, ``B`` R2-R4 and for ``C`` R5
is the 1k resistor. If we want to compact the ``Source BoM`` column we
just need to enable the ``source_by_id`` option:

.. code:: yaml

   kibot:
     version: 1

   outputs:
     - name: 'bom_csv'
       comment: "Bill of Materials in CSV format"
       type: bom
       dir: BoM
       options:
         use_alt: true
         number: 10
         ref_id: 'A:'
         source_by_id: true
         aggregate:
           - file: tests/board_samples/kicad_5/merge_2.sch
             number: 20
             ref_id: 'B:'
           - file: tests/board_samples/kicad_5/merge_3.sch
             number: 30
             ref_id: 'C:'

And we’ll get:

+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| Row      | Description      | Part | References | Value | Footprint | Quantity | Build    | Status | Datasheet | Source BoM |
|          |                  |      |            |       |           | Per PCB  | quantity |        |           |            |
+==========+==================+======+============+=======+===========+==========+==========+========+===========+============+
| 1        | Unpolarized      | C    | A:C1 B:C2  | 1nF   |           | 2        | 30       |        | ~         | A:(1)      |
|          | capacitor        |      |            |       |           |          |          |        |           | B:(1)      |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 2        | Unpolarized      | C    | A:C2 B:C1  | 10nF  |           | 2        | 30       |        | ~         | A:(1)      |
|          | capacitor        |      |            |       |           |          |          |        |           | B:(1)      |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 3        | Resistor         | R    | A:R1-A:R3  | 1k    |           | 7        | 120      |        | ~         | A:(3)      |
|          |                  |      | B:R2-B:R4  |       |           |          |          |        |           | B:(3)      |
|          |                  |      | C:R5       |       |           |          |          |        |           | C:(1)      |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+
| 4        | Resistor         | R    | B:R1       | 10k   |           | 5        | 140      |        | ~         | B:(1)      |
|          |                  |      | C:R1-C:R4  |       |           |          |          |        |           | C:(4)      |
+----------+------------------+------+------------+-------+-----------+----------+----------+--------+-----------+------------+


.. index::
   pair: Bill of Materials; KiCad BoM options
   pair: Bill of Materials; BoM options from KiCad

.. _bom_kicad_options:

Using KiCad's internal BoM options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modern KiCad allows editing the BoM generation using a dialog. You can select
which fields are used, their order, how they are grouped, their sorting, etc.
These options are stored in the project file. You can import them using
something like this:

.. code:: yaml

   kibot:
     version: 1

   outputs:
     - name: 'bom_kicad_test'
       comment: "Bill of Materials using KiCad settings"
       type: bom
       options:
         format: KICAD
         ignore_dnf: false
         group_not_fitted: true
         group_fields: []
         sort_style: kicad_bom
         columns:
           - _kicad_bom_fields

Here is what the options do:

- **format**: Choosing KiCad the output format will mimic the file generated by
  KiCad. Usually you'll want to select another format.
- **ignore_dnf**: Do Not Fit componets goes to the same list, not separated
- **group_not_fitted**: Not fitted components are grouped with fitted components
- **group_fields**: An empty list so they get imported from KiCad
- **sort_style**: Use the sorting as specified by KiCad
- **columns**: The *_kicad_bom_fields* will be replaced by the fields specified
  in the project. The fields used for grouping will be added to the
  **group_fields**, as we defined it empty we'll get the same grouping criteria.

You can add any of the KiBot's options. So you could generate a nice HTML BoM
but using the fields selected in KiCad's GUI.

.. note::
   The string filter must be implemented using filters, we don't import it from
   the project.

   If you need to include DNP components (don't confuse it with "Excluded from BoM")
   you should disable the `kicad_dnp_applied` global option.


.. index::
   pair: Bill of Materials; columns internal
   pair: Bill of Materials; special columns

.. _bom_columns:

Columns available for the BoM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to all the user defined fields you also have the following columns:

-  **Build Quantity**: How many components we use for this row for all the PCBs.
-  **Datasheet**: The datasheet from the standard field.
-  **Description**: The description from the component library (DCM file).
   Note that a user field with the same name has more precedence.
-  **${DNP}**: Is **DNP** when the schematic DNP attribute is enabled, for compatibility with KiCad BoM.
-  **${EXCLUDE_FROM_BOARD}**: Is **Excluded from board** when the schematic *exclude from board*
   attribute is enabled, for compatibility with KiCad BoM.
-  **${EXCLUDE_FROM_SIM}**: Is **Excluded from simulation** when the schematic *exclude from simulation*
   attribute is enabled, for compatibility with KiCad BoM.
-  **Footprint**: The name of the footprint, without the library name.
-  **Footprint Lib**: The name of the library for the footprint.
-  **Footprint Full**: The full name for the footprint (LIB:NAME).
-  **Footprint Populate**: If the footprint is populated (soldered) or not, can be: *yes* or *no*.
   Affected by the **footprint_populate_values** option.
-  **Footprint Rot**: The rotation angle for the footprint.
-  **Footprint Side**: The side of the footprint, *bottom* or *top*.
-  **Footprint Type**: The type of the footprint, can be: *SMD*, *THT* or *VIRTUAL*.
-  **Footprint Type NV**: The type of the footprint, can be: *SMD* or *THT*. Empty if not defined.
   Affected by the **footprint_type_values** option.
-  **Footprint X**: The X coordinate for the footprint.
-  **Footprint Y**: The Y coordinate for the footprint.
-  **Footprint X-Size**: The footprint width, no rotation computed.
-  **Footprint Y-Size**: The footprint height, no rotation computed.
-  **${ITEM_NUMBER}**: Same as **Row**, for compatibility with KiCad BoM.
-  **Net Name**: Name of the nets associated with the footprint. Useful for testpoints.
-  **Net Label**: Name of the nets associated with the footprint without the path. Useful for testpoints.
-  **Net Class**: Name of the net classes associated with the footprint. Useful for testpoints.
-  **Part**: The name of the symbol for the component, without the library name.
-  **Part Lib**: The name of the library for the symbol.
-  **${QUANTITY}**: Same as **Quantity Per PCB**, for compatibility with KiCad BoM.
-  **Quantity Per PCB**: How many components we use for this row for each PCB.
-  **References**: The component references.
-  **Row**: The row number in the BoM for this entry.
-  **Sheetpath**: The path in the schematic hierarchy for the component.
-  **Source BoM**: From which BoM/s comes this component/s. This is used when consolidating more than one BoM.
-  **Status**: The DNF (Do Not Fit) and/or DNC (Do Not Change) status for the component.
-  **Value**: The value for the component. Affected by the **normalize_values** option.

Most of the footprint columns are oriented to the creation of position files using the BoM output,
for more information consult :ref:`xyrs_files`.


.. index::
   pair: outputs; extend

Using other output as base for a new one
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to define an output that is similar to another, and you want
to avoid copying the options from the former, you can *extend* an
output. To achieve it just specify the name of the base output in the
``extends`` value. Note that this will use the ``options`` of the other
output as base, not other data as the comment.

Also note that you can use `YAML
anchors <https://www.educative.io/blog/advanced-yaml-syntax-cheatsheet#anchors>`__,
but this won’t work if you are importing the base output from other
file.

Additionally you must be aware that extending an output doesn’t disable
the base output. If you need to disable the original output use
``disable_run_by_default`` option.



.. index::
   pair: outputs; groups

.. _grouping-outputs:

Grouping outputs
^^^^^^^^^^^^^^^^

Sometimes you want to generate various outputs together. An example
could be the fabrication files, or the documentation for the project.

To explain it we will use an example where you have six outputs. Three
are used for fabrication: ``gerbers``, ``excellon_drill`` and
``position``. Another three are used for documentation: ``SVG``,
``PcbDraw`` and ``PcbDraw2``. The YAML config containing this example
can be found `here <tests/yaml_samples/groups_1.kibot.yaml>`__. If you
need to generate the fabrication outputs you must run:

::

   kibot gerbers excellon_drill position

One mechanism to group the outputs is to create a ``compress`` output
that just includes the outputs you want to group. Here is one example:

.. code:: yaml

     - name: compress_fab
       comment: "Generates a ZIP file with all the fab outputs"
       type: compress
       run_by_default: false
       options:
         files:
           - from_output: gerbers
           - from_output: excellon_drill
           - from_output: position

The ``compress_fab`` output will generate the ``gerbers``,
``excellon_drill`` and ``position`` outputs. Then it will create a ZIP
file containing the files generated by these outputs. The command line
invocation for this is:

::

   kibot compress_fab

Using this mechanism you are forced to create a compressed output. To
avoid it you can use ``groups``. The ``groups`` section is used to
create groups of outputs. Here is the example for fabrication files:

.. code:: yaml

   groups:
     - name: fab
       outputs:
         - gerbers
         - excellon_drill
         - position

So now you can just run:

::

   kibot fab

The ``gerbers``, ``excellon_drill`` and ``position`` outputs will be
generated without the need to generate an extra file. Groups can be
nested, here is an example:

.. code:: yaml

   groups:
     - name: fab
       outputs:
         - gerbers
         - excellon_drill
         - position
     - name: plot
       outputs:
         - SVG
         - PcbDraw
         - PcbDraw2
     - name: fab_svg
       outputs:
         - fab
         - SVG

Here the ``fab_svg`` group will contain ``gerbers``, ``excellon_drill``,
``position`` and ``SVG``.

Groups can be imported from another YAML file.

Avoid naming groups using ``_`` as first character. These names are
reserved for KiBot.


.. index::
   pair: Print PCB; images from outputs

.. _add_print_images:

Adding images from an output to the PCB print
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When printing your PCB using `pcb_print` you can add images generated by a
renderer output (i.e. `pcbdraw`, `render_3d`, `blender_export`).

To do it you must create a KiCad group named **kibot_image_OUTPUT** where
*OUTPUT* is the name of the output that will generate the image. If you
don't know how to create a group consult :ref:`create_group`.

.. note::

   The image must be in PNG format, other formats aren't currently supported.

The image will be associated with the layer of the first element in the group.
So when you print this layer you'll get the image at the position of the group.

The image will be drawn inside the group, but the aspect ratio will be
preserved. So you'll get the best results if the group aspect ratio matches
the image aspect ratio.


.. index::
   pair: PCB group; Create a group

.. _create_group:

Creating a group in your PCB
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Various outputs and preflights uses a PCB group to specify the position and
size of the target object to be placed in your PCB. Here we explain how to
create a group.

- Select the layer you want to use.
- Draw a rectangle with the size and position you desire.
- Draw another thing inside the rectangle, i.e. a text describing the group
- Select both and create a group (right mouse button, then *Grouping* -> *Group*).

.. note::

   You might also just create a text box and select it, KiCad allows creating a
   group with just one element

- Now edit the group and change its name according to the name specified by
  the output or preflight.

.. note::

  For the `Draw Fancy Stackup` and `Include Table` preflights, the font can be
  set by adding to the group a textbox with the desired font. You can leave the
  textbox empty and hide the borders.