.. index::
   single: Changelog

.. _Changelog:

Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a
Changelog <https://keepachangelog.com/en/1.0.0/>`__, and this project
adheres to `Semantic
Versioning <https://semver.org/spec/v2.0.0.html>`__.

`1.9.2 <https://github.com/INTI-CMNB/KiBot/compare/v1.9.1...dev>`__ - Unreleased
--------------------------------------------------------------------------------

Added
~~~~~

-  \*SCH Print:

   -  ’draw_hop_over\` to draw it at wire crossings
   -  Better sub-sheet names handling for KiCad 10+

-  Gerber/DXF/PDF/PS/SVG:

   -  ``sheet_reference_layout``: to specify another worksheet (KiCad
      11)
   -  ``common_layers``: list of layers to use on every page (KiCad 11)

-  DXF:

   -  ``single_file``: to plot all layers to a single file (KiCad 11)

-  PDF:

   -  ``single_page``: used with ``single_file`` to get just one page
      (KiCad 11)
   -  ``background_color``: to select a particular background color
      (KiCad 11)
   -  ``exclude_metadata``: no metadata (KiCad 11)
   -  ``author``: overrides the AUTHOR (KiCad 11)
   -  ``subject``: overrides the SUBJECT (KiCad 11)
   -  ``front_footprint_property_popups`` and
      ``back_footprint_property_popups``: To control information about
      the footprints (KiCad 11)

-  PDF SCH Print:

   -  ``exclude_property_popups``: no properties popups (smaller size)
   -  ``exclude_hierarchical_links``: no links to sub-sheets
   -  ``exclude_metadata``: no metadata
   -  ``author``: overrides the AUTHOR
   -  ``subject``: overrides the SUBJECT

-  PS/SVG/PDF:

   -  ``monochrome`` and ``color_theme``: to generate color PSs (KiCad
      11)
   -  ``single_file``: to plot all layers to a single file (KiCad 11)
   -  ``mirror``: alias for ``mirror_plot``
   -  ``negative``: alias for ``negative_plot``

-  KiCad 11:

   -  Global:

      -  ``kicad_cross_mechanism``: selects cross/hide/sketch when using
         KiCad’s internal mechanism for crossing components in Fab
         layers

   -  Gerber:

      -  ``sketch_pad_numbers``: when sketching the pads in Fab layers
         also add the pad number

Fixed
-----

-  Quick Start: avoid including HPGL for KiCad 10
-  KiBot Check:

   -  Mark KiCad 10 as good (green, not red)
   -  Avoid bogus messages when importing pcbnew (KiCad 10 workaround)

-  Navigate Results:

   -  Rotated PostScript for the PCB Print output

-  PcbDraw:

   -  ‘svg_paths’ mode for ‘size_detection’ avoids stuff outside the PCB
      and mirror issues. We still recommend using the default.

Changed
=======

-  Gerber/PS/PDF/SVG/DXF:

   -  ``exclude_pads_from_silkscreen`` is no longer valid (just warning)
      was for KiCad 5

-  Gerber/PS/PDF/SVG:

   -  ``line_width`` is no longer valid (just warning) was for KiCad 5

-  PcbDraw:

   -  Updated to v1.4.0 base code, expect some subtle differences.

`1.9.1 <https://github.com/INTI-CMNB/KiBot/compare/v1.9.0...v1.9.1>`__ - 2026-07-28
-----------------------------------------------------------------------------------

.. _added-1:

Added
~~~~~

-  Support for Python 3.14 (#930)
-  CLI:

   -  –keep-temporals: to keep temporal files

-  Some limited support for the VARIANT and VARIANT_DESC variables found
   in KiCad 10. They can be used for things like 3D and print_pcb even
   for KiCad 6.
-  Workaround for KiCad 10 bug 14360 which prevents native QRs to be
   updated when they use a KiCad variable.
-  Schematic:

   -  Support for SHEETNAME, SHEETFILE and SHEETPATH in the title block
   -  Support for the ``jumper_pin_groups`` attribute of symbols. (#942)
   -  Some support for properties defined at sheet level. (#941)

-  Globals:

   -  ``schematic_sheet_name_workaround`` to workaround SHEETNAME on
      page 1 (See #933)
   -  ``pcb_material_color`` default color for the PCB core material
   -  ``solder_paste_color`` default color for the solder paste
   -  ``remove_3D_models_for_dnp`` to disable 3D models removal from
      variants

-  Variants:

   -  pre_transform filter to KiCad variants

-  E/DRC:

   -  Dark mode support and icon to select it.

-  Blender Export:

   -  Added support for PCB2Blender 2.17 format

-  BoM:

   -  JSON output format. As a helper for external renderers (See #917)
   -  Dark mode support and icon to select it.

-  Diff:

   -  ``tag_filter``: to select which tags are used for KIBOT_TAG

-  KiCad Site:

   -  ``bom`` configuration
   -  ``kiri`` configuration

-  KiRi:

   -  ``commits`` and ``labels`` options to include an explicit list of
      git revisions (hashes, tags, branches, etc.) (#946)
   -  ``include_dirty`` to exclude the local changes. (#946)

-  Panelize:

   -  Better support for ``renameref`` use. Now we set the reference
      from the PCB when global ``use_pcb_fields`` variable is enabled.

-  PcbDraw:

   -  ``show_copper`` to disable tracks and zones (from 1.2.0)

-  Render 3D:

   -  KiCad 10: support for kicad-cli interface, adds some new options
      but has various limitations, hopping they will be fixed.

-  Report:

   -  All PDF pages are included, not just the first
   -  The full report now works with SVGs and PDFs for both (SCH and
      PCB), SVGs have priority
   -  ``remove_split_pdfs``: To control if we remove split PDFs
   -  ``collect_images``: To just avoid collecting images, enabled by
      default when generating a CSV. Avoids unintended infinite loops.
      (See #931)

-  \*SCH Print

   -  ``title_propagate``: The title is not only set for page 1 but also
      for all pages.

.. _fixed-1:

Fixed
-----

-  Warnings:

   -  11 and 148 were always filtered for CI/CD, even when using
      –warn-ci-cd
   -  Crash when missing basic fields, KiCad 6+
   -  Avoid warning about datasheet mismatch when creating a component
      from the PCB.

-  CLI:

   -  When using a –variant and an specific target, it was generated for
      the first variant in the list, not the rest

-  Filters:

   -  Applied only to the first copy of a KiKit panel with default
      ``renameref`` (#937)

-  Gerber Drill:

   -  Avoid showing an error when KiCad 10 skips a drill file (See #928)

-  KiRi:

   -  ``kiri_server`` path to the HTML

-  \*SCH Print:

   -  The list of targets now includes all schematic pages
   -  Output when the ``output`` option was empty
   -  DNP components when no variant is used and we set a title or
      replace images (``kibot_image_OUTPUT``) (#943)

-  PCB2Blender Tools:

   -  Crash for oblong drills

-  PCB Stats:

   -  Missing targets (See #928)

-  PDFUnite:

   -  Using just the first page when using the internal joiner (#950)

-  SCH/PCB Variant:

   -  “Exclude from bom” flag wrongly exported

-  Report:

   -  Now all SVG schematic pages are included, not just the first

-  VRML

   -  Avoid WRL files for KiCad 10 (See #928)

-  Now we clear fields created by a variant, so they don’t interfere in
   multiple variants generation.

.. _changed-1:

Changed
-------

-  E/DRC and BoM: As we now have dark mode support the CSS is more
   complex and user defined CSSs might need some adjusts
-  Now when an output runs another outputs as dependencies the name of
   the created output is displayed.
-  When using ``pcb_print`` and including tables you no longer need to
   run the output that generates the CSV first, it gets generated
   on-the-fly
-  Report: the outputs that generates images no longer needs to be
   already executed, KiBot will run them
-  More common CI/CD warnings filtered:

   -  W008 Unable to find KiCad configuration file
   -  W058 Missing KiCad main config file
   -  W058 Missing default system table

-  No more reports on PCB/SCH fields mismatch when the variants modified
   the field
-  Avoid more than 20 levels of nested outputs, this is an infinite
   loop.
-  Quick Start:

   -  Use ``force_stackup_colors`` for ``render_3d``

.. _section-1:

`1.9.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.8.5...v1.9.0>`__ - 2026-05-12
-----------------------------------------------------------------------------------

.. _added-2:

Added
~~~~~

-  New outputs:

   -  BoM Labels (bom_labels): [Experimental] To generate a PDF
      containing labels for the BoM items. (#886)
   -  PCB stats (pcb_stats): The KiCad 10 PCB statistics
   -  Hugo KiCad Site helper (kicad_site): [Experimental] Helper for the
      Hugo theme for KiCad projects (#917)

-  CLI:

   -  –fail-on-warnings: to return error when we detected warning (See
      #828)
   -  –warn-all: to display some warnings that you’ll find during common
      use

-  Schematic:

   -  Support for private text on symbols (#914)
   -  Some basic check for the page numbers

-  New filters:

   -  ``alternatives``: Used to add alternative fields (i.e. alternative
      manufacturers) (#913)

-  generic filter: ``exclude_kicad_dnp`` to exclude components marked as
   DNP in KiCad (See #887)
-  Variants: Experimental KiCad variants
-  KiCad 9 embedded files: populate the cache if needed (See #890)
-  preflights:

   -  Mechanism to merge preflights from imports (``merge_pre``) (#900)
   -  ``set_text_variables_sheet_title``,
      ``set_text_variables_sheet_title_min`` and
      ``set_text_variables_sheet_title_default`` global options to
      enable the generation of KiCad variables containing the titles for
      all the schematic sheets. The are named ``SHEET_TITLE_n``

-  Global options:

   -  ``allow_blind_vias`` and ``allow_buried_vias``: for KiCad 10 to
      replace the unified ``allow_blind_buried_vias``
   -  ``code_page_fallback``: to specify a code page for text not
      encoded in UTF-8

-  3D models: option to download the latest 3D models
   (``kicad_3d_url_version``) (See #899)
-  BoM:

   -  descriptive error when using ``kicad`` format and no options
      found.
   -  ``tilde_is_empty`` to interpret fields defined as ``~`` as empty.
   -  ``sep_for_merged`` to configure the separator for multiple values
      on the same field. This is when a group contains components with a
      difference in the field.
   -  ``merge_values`` to also merge different values on grouped
      components.

-  Download Datasheets: now uses ``curl`` if installed.
-  DRC/ERC: Configurable logo (#889)
-  iBoM: ``mark_when_checked`` option (#881)
-  KiRi: Support for uninitialized submodules (#888)
-  Navigate results: ``expand_text_vars`` to expand %X and vars in the
   title.
-  Panelize: ``copy_lib_tables`` to get a usable lib table
-  PcbDraw:

   -  Allow huge files, usually from panels.
   -  Better performance

-  Position:

   -  ``grid``/``grid_fail`` options to check if components are in a
      grid

-  Report: ``buried_vias_count`` for KiCad 10
-  SCH/PCB Variant: ``include`` option to export legacy variants to
   KiCad 10
-  SCH Print: specify pages to be included (#907)

.. _fixed-2:

Fixed
~~~~~

-  3D models:

   -  Download models from the repo tag corresponding to the currently
      installed KiCad version, not the one from ``master`` (#899)
   -  EasyEDA 3D models download issues when the specified model was an
      STEP file using an extension different than ``.step`` (#921)

-  Blender export: problems with component values containing ``/``
   (#885)
-  BoM:

   -  ``Missing footprint information for`` for components marked as not
      on board.
   -  Digi-Key URLs, to adapt the new format
   -  HTML: link cells not marked empty

-  DRC:

   -  No schematic parity check when using ``check_zone_fills`` and not
      ``fill_zones`` (#920)

-  Panelize:

   -  Problems when using angles (#898)
   -  Confusing error when the output wasn’t generated

-  PCB Print: worksheet page 1 vs other pages look when using the
   internal mechanism (#903)
-  Allow empty ``dir`` option

.. _changed-2:

Changed
~~~~~~~

-  ``--fail-on-warnings`` now ignores filtered warning (as the help
   suggested) and you can get the old behavior adding
   ``--fail-on-ignored`` (#893)
-  3D models: GitLab URL. Because the old URL is now blocked.
-  W009 and W044 warnings promoted to “common use” warnings
-  E/DRC: we now get the big OK mark when all violations are excluded
-  BoM: by default fields defined as ``~`` are empty.

.. _section-2:

`1.8.5 <https://github.com/INTI-CMNB/KiBot/compare/v1.8.4...v1.8.5>`__ - 2025-11-26
-----------------------------------------------------------------------------------

.. _added-3:

Added
~~~~~

-  CLI:

   -  -F, –fail-on-ignored: to return error even when using -D (#828)

-  Schematic: Support for private fields (#812)
-  Global options:

   -  ``update_pcb_text_cache``: Used to copy the text variables from
      the project to the PCB file (#860 #861)
   -  ``disable_kicad_cross_on_fab``: To avoid KiCad 9 crosses on Fab
      layer, so only KiBot controls it (#866)

-  Internal templates:

   -  PCB2Blender_2_17: generates a pcb2blender 2.17 file to import on
      Blender

-  Pre-flights:

   -  ``check_field``: option to exclude components from a check (#848)

-  Variants:

   -  Sub-boards: now you can specify a contour in an arbitrary layer.
      (See yaqwsx/KiKit#846)

-  PCB2Blender_Tools: Experimental v2.17 file generation
-  Report: separated N/PTH slot sizes (#824)
-  VRML: workaround for KiCad 9 randomly failing to copy 3D models
   (#804)
-  Navigate Results, PCB Print, PcbDraw: Support for big SVGs (#851)
-  PCB Print: Workaround for KiCad 9.0.5 change in how holes are plotted
   when a layer is not included (black instead of white).
-  Export_3D: ``center`` option to ``origin`` (#871)
-  Compress/Copy Files: Now ``dest`` also expands %X patterns (can be
   disabled) (#873)
-  Worksheet: Support for paths relative to the project (#879)
-  Blender Export: Support for STL/OBJ/PLY/GLTF changes in Blender 4.2
   (#880)

.. _fixed-3:

Fixed
~~~~~

-  User.N layer numbering. I.e. pcb_print issues with their numbering
   (#808)
-  KiCost: ``kicost_config`` not working (#815)
-  Huge memory usage for panels (#842)
-  Panelize: vjustify wrong choices (were the same as hjustify) (#846)
-  THT Resistors: Problems when using the STEP version of the model
   (#856)
-  Fancy stackup:

   -  Limit the decimals of the copper weight to 2 (#864)
   -  Buried vias issues on KiCad 9 (#870)

-  Draw stackup, Print drill table, Include table:

   -  Workaround for KiCad 9.0.5 broken API to GetTextBox

.. _changed-3:

Changed
~~~~~~~

-  Filtered KiBot warnings are informed in the debug output (See #817)

.. _section-3:

`1.8.4 <https://github.com/INTI-CMNB/KiBot/compare/v1.8.3...v1.8.4>`__ - 2025-04-03
-----------------------------------------------------------------------------------

.. _added-4:

Added
~~~~~

-  Support for the broken API in KiCad 9.0.1

   -  Change in the names of various constants
   -  Removed the SetPlotInvisibleText plot option
   -  Change in the SetPlotOnAllLayersSelection call

-  Schematic:

   -  Support for files embedded on symbols (#802)
   -  Support for embedded worksheets

-  BoM:

   -  ``Footprint Full`` virtual field for the ``LIB:FOOTPRINT`` name
   -  ``kicad_dnp_applied`` option to overwrite the global option

.. _fixed-4:

Fixed
~~~~~

-  3D outputs with variants: Use of the ${PROJECTNAME} KiCad variable
   (#801)
-  3D outputs: Embedded 3D models misinterpreted as KiCad 6 aliases (See
   #802)

.. _section-4:

`1.8.3 <https://github.com/INTI-CMNB/KiBot/compare/v1.8.2...v1.8.3>`__ - 2025-03-18
-----------------------------------------------------------------------------------

.. _added-5:

Added
~~~~~

-  New outputs:

   -  ODB: Exports the PCB in ODB++ format (KiCad 9) (#782)
   -  IPC2581: Exports the PCB in IPC-2581 (IPC-DPMX) format (KiCad 9)
   -  export_3d: Exports the 3D model of the PCB in BREP, GLB, STL, STEP
      and XAO (KiCad 9) (#783)
   -  jobset: Runs a KiCad jobset (KiCad 9)

-  CLI:

   -  ``--variant`` to specify which variants will be generated (See
      #737)
   -  ``--defs-from-project`` allows using KiCad variables for the
      preprocessor (See #643)

-  Variants and filters:

   -  Outputs with variants can now specify an ``exclude_filter`` in
      addition to the variant. Like it was possible for transform and
      dnf

-  Preflights:

   -  ``consolidate_pcbs``: Used to merge PCBs before creating 3D
      stacked renders (#728)
   -  ``expand_in_command`` option to ``set_text_variables``, used to
      expand %X patterns in the command (#746)
   -  ``check_fields`` mechanism to check for extra fields (#774)

-  Global options:

   -  ``work_layer``: to choose the temporal layer for internal
      operations (#713)

-  Internal templates:

   -  ``_KIBOT_DRILL_AUX_ORIGIN`` option to control drill, position and
      gerber origin

-  Workaround for people using backslashes (i.e. Windows+WSL) (#719)
   (#607) More general than in previous versions.
-  Blender Export: option to avoid soldering heatsinks
-  Boardview: OBDATA support
-  BoM:

   -  Field aliases ${QUANTITY} and ${ITEM_NUMBER} for compatibility
      with KiCad’s internal BoM.
   -  Fields ${DNP}, ${EXCLUDE_FROM_BOARD} and ${EXCLUDE_FROM_SIM}, like
      the ones used by KiCad’s internal BoM.
   -  Using ``_kicad_bom_fields`` in the list of columns now you can
      import the fields from the KiCad’s internal BoM.
   -  New option ``group_not_fitted`` to group not fitted components
      with fitted components. For compatibility with KiCad’s internal
      BoM.
   -  New option ``sort_ascending`` to sort in reverse order
   -  New sort style: *kicad_bom*, uses the field an ascending used by
      KiCad’s BoM
   -  ``ref_range_separator`` option to configure the character used for
      reference ranges
   -  ``use_ref_ranges`` alias for ``use_alt``
   -  New *kicad* format to mimic KiCad’s internal BoM.
   -  ``right_digits`` option to control the decimals for position
      fields (#739)
   -  New ``sort_style`` named ``field`` and ``sort_field`` option to
      sort by one or more arbitrary fields.
   -  New ``csv`` options: (to match KiCad internal BoM functionality)

      -  ``string_delimiter`` to configure the quote character
      -  ``keep_line_breaks`` to remove line breaks in fields
      -  ``keep_tabs`` to remove tabs in fields

-  Draw Fancy Stackup:

   -  ``border_thickness``: Thickness of the borders of stackup drawing
      and stackup table (#747)
   -  A mechanism to set the font, using a text box (#748)

-  Drill:

   -  Option to don’t generate the drill files, so you can generate only
      the maps (#720)
   -  Option to generate a drill table (#760)

-  Include table:

   -  A mechanism to set the font, using a text box (#748)
   -  ``force_font_width`` to force a font width (#752)

-  Navigate Results:

   -  New flavor “navigate_results_rb” with a “reactive” look (#768)

-  Netlist:

   -  OrcadPCB2, Allegro, CADSTAR, PADS, KiCad XML, Spice and Spice
      model formats

-  PCB Print:

   -  A mechanism to filter components for a particular layer (#706)
   -  Workaround for Ghostscript handling %d wrong when followed by an
      hex digit (#763)
   -  Now you can include drill maps using ``drill_pairs`` as
      ``repeat_layers`` (#764)

-  Report:

   -  ``top_total``, ``bot_total``, ``total_smd``, ``total_tht`` and
      ``total_all`` component counts (See #730)
   -  Also versions of the counters for excluded (exc), not fitted (dnp)
      and not changed (dnc) (See #730)
   -  ``total_components`` template, intended to generate CSV files with
      component counts (See #730)
   -  Now you can use expressions like ${V1+V2}
   -  ``mm_digits``, ``mils_digits`` and ``in_digits`` to change the
      number of digits for unit conversions (#745)
   -  ``display_trailing_zeros`` to show trailing zeros (#745)
   -  \*_cap\* sufix to capitalize strings (#745)
   -  *h2h*, *c2h* and *c2e* Hole to Hole, Hole to Copper and Copper to
      Edge info (KiCad 6+) (#745)
   -  *pad_drill_pth*, *pad_drill_npth* (and similars) for PTH/NPTH
      specific drill dimensions (#745)
   -  ``csv_remove_leading_spaces`` to remove leading spaces/tabs after
      CSV separator (useful to generate CSV from a .txt template where
      elements are aligned for easier reading) (#745)
   -  A mechanism to get the names of the files generated by an output.
      The variables are named OUTPUT_outpath_INDEX (#761)

-  SCH Variant and \*SCH Print:

   -  A mechanism to paste images from outputs (#714)

-  \*SCH Print:

   -  Default font for KiCad 9 (#691)

.. _fixed-5:

Fixed
~~~~~

-  Definitions: avoid interpreting empty definitions as the “None”
   string (See #757)
-  Guess for 3rd party dir: not just for v6
-  SubParts filter:

   -  iBoM and Schematic print didn’t take it into account (#716)
   -  Any output filtering by reference ignored them (#729)

-  BoM

   -  The field name ``Reference`` was accepted, but didn’t work
   -  Missing footprint information for sub-units (#741)
   -  XLSX logo scale (#750)

-  Do Not Fit footprint crosses:

   -  Problems with footprints where the center isn’t the geometric
      center (#725)

-  DRC:

   -  Zone refill issues with the new DRC preflight (#759)

-  Draw Fancy Stackup:

   -  Problems drawing micro vias (#749)
   -  Confusing drawing when symmetric vias overlap

-  Drill:

   -  Via pairs overwritten by PTH files (#758)

-  Navigate Results:

   -  Problems when using ``erc: true`` or ``drc: true`` (#742)

-  PCB Print:

   -  Problems when using the default worksheet and the internal frame
      plotter (#767)
   -  Some layer options (use_for_center, sketch_pads_on_fab_layers and
      exclude_filter) not copied on repeated layers
   -  ``sketch_pads_on_fab_layers`` not inherited from parent when using
      layer names (See #777)

.. _changed-4:

Changed
~~~~~~~

-  Default temporal layer for internal use is now “Margin”, instead of
   “User.9”
-  Draw Fancy Stackup:

   -  Micro vias to look closer to real world, they only span 2 layers
      and they must be stacked to span more layers.

-  Renderers:

   -  Components marked by the exclude filter, or marked virtual, were
      excluded from the 3D models and solder paste processing, but the
      docs says this is just for BoM (See #772)

.. _section-5:

`1.8.2 <https://github.com/INTI-CMNB/KiBot/compare/v1.8.1...v1.8.2>`__ - 2024-10-28
-----------------------------------------------------------------------------------

.. _added-6:

Added
~~~~~

-  Experimental GUI
-  Preflights:

   -  Draw Fancy Stackup: which includes the type of vias used (#699)
   -  Include Table: used to include CSV tables generated by
      bom/position outputs (#702)

-  Globals:

   -  ``dnp_cross_top_layer`` and ``dnp_cross_bottom_layer``: to control
      the layer where footprints are crossed. (#700 and #622)

-  SVG: ``use_aux_axis_as_origin`` option (#681)
-  Report: thickness units (#685)
-  PCB Print:

   -  Worksheet: undocumented font face and color now can be used (See
      #695)

-  Panelize:

   -  ``copy_vias_on_mask`` option to workaround KiCad’s bug 18991 (See
      #703 and #704)

.. _fixed-6:

Fixed
~~~~~

-  BoM: Sub-PCBs not applied (#697)
-  Copy Files: problems when using from compress and using worksheets.
-  Export Project: problems when downloading KiCad models and trying to
   compress the result.
-  PcbDraw: problems with 0 ohms THT resistors (#689)
-  PCB Print:

   -  Allow specifying ``repeat_for_layer`` with empty
      ``repeat_layers``. This was the old behavior (i.e. 1.7.0) (#671)
   -  Problems with drill marks on KiCad 8.0.4+, which prints them in
      every single layer (even technical ones) (#696)
   -  When trying to force a WKS and the project didn’t define a WKS.
      The “gui” strategy failed to use the specified WKS

-  Draw stackup:

   -  Segmentation Fault on KiCad 8 when creating a new group
   -  Units not applied when creating a new group

-  Expansion of internal field names. KiCad expands “VALUE”, not
   “Value”, which is what you see in the GUI

.. _changed-5:

Changed
~~~~~~~

-  Quick Start:

   -  Diff/KiRi: Avoid creating when we don’t have at least 2 to compare

-  PCB Print:

   -  Avoid ``colored_pads`` and ``colored_vias`` side effects (#682)

-  BoM:

   -  Avoid leaking DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET in logs

.. _section-6:

`1.8.1 <https://github.com/INTI-CMNB/KiBot/compare/v1.8.0...v1.8.1>`__ - 2024-09-25
-----------------------------------------------------------------------------------

.. _fixed-7:

Fixed
~~~~~

-  Blender Export:

   -  Stacked boards when using an automatically generated PCB3D.
   -  Point of view when using the human names instead of the axis
      names.

-  Footprint variant (created by Var Replace filter):

   -  Flipped components didn’t get flipped after replacement (#664)
   -  Problems generating drill outputs (#663)

-  PCB print: errors when printing a fully empty layer

.. _section-7:

`1.8.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.7.0...v1.8.0>`__ - 2024-09-17
-----------------------------------------------------------------------------------

.. _added-7:

Added
~~~~~

-  Experimental Altium PCB conversion (#625)
-  Most places where a field is expected now support ``_field_*`` to
   fetch the globally defined value.
-  Preflights:

   -  check_fields: used to ensure conditions on desired fields (#643)
   -  e/drc: option to force english messages (needed for KiCad 8.0.4)

-  Filters:

   -  ``separate_pins``: used to create testpoint reports (#638)
   -  ``_null`` can be used to skip the filters processing

-  Global options:

   -  ``use_pcb_fields``: allows using fields defined in the PCB (and
      not only in the schematic), enabled by default (#648 and #650)
   -  ``field_current``: to specify the field used for current ratings

-  Internal templates:

   -  Testpoints_by_attr, Testpoints_by_attr_CSV,
      Testpoints_by_attr_HTML, Testpoints_by_value,
      Testpoints_by_value_CSV and Testpoints_by_value_HTML: Used to
      generate testpoint reports (#638)

-  Command line:

   -  Option to also list sub-PCBs found in variants

-  BoardView: support for BVR format
-  BoM: logo file name can contain env vars and/or ~ (#620)
-  Datasheet: option to classify the datasheets by reference.
-  KiCost: option to specify a configuration file (#615)
-  Report:

   -  Solder paste usage stats (#616)
   -  Support for variants (See #616)
   -  Testpoints report (See #638)

-  xDRC: configurable category (#647)
-  Schematic:

   -  Support for text boxes inside symbols (#621)

-  Worksheet:

   -  Support for KiCad 8 bitmaps (#623)

-  Position:

   -  Support for panels repeating the same component (See #656)

.. _fixed-8:

Fixed:
~~~~~~

-  iBoM: *highlight_pin1* option didn’t allow the use of the new
   choices.
-  PCB2Blender_Tools: transform filters might make it fail. (#618)
-  BoM:

   -  No color reference when using row colors but not column or kicost
      colors. (#619)
   -  “0 pico” for “0”
   -  Use of ``lcsc_link`` as boolean
   -  User fields for components that are only in the PCB not filled
      (#656)

-  Worksheet: Size of PNGs that specify its PPI resolution.
-  Filters:

   -  Problems with filters that change fields for components that are
      only in the PCB. (#628)
   -  Use of ’\_none’ filter in lists of filters and \_kf()

-  Variants:

   -  Problems when remove_solder_paste_for_dnp and
      remove_adhesive_for_dnp are both disabled
      (remove_solder_mask_for_dnp wrongly defined) (#632)
   -  Problems when using ``set_text_variables_before_output`` (#649)

-  Draw Stackup:

   -  Dimension always drawn on User.Drawings layer (#629)
   -  Problems when the PCB wasn’t loaded by another preflight

-  Update XML: ``check_pcb_parity`` not usable for KiCad 8, must use the
   ``drc`` preflight (#633)
-  PCB Print: %ln and %ll substitution when using ``repeat_for_layer``
   option
-  Render_3D: bottom side components that doesn’t rotate from its center
   got displaced highlight (#659)
-  QR Lib output and various preflights: might remove DRC exclusions.
   This is a KiCad bug that we must workaround (#653)
-  3D outputs: temporal .kicad_dru file not removed (#655)
-  Generated PCB files: problems with some big structures, like zone
   fills, that could generate huge lines in the generated PCB, not
   supported by KiCad. (#660)

.. _changed-6:

Changed:
~~~~~~~~

-  KiCad 8.0.2: The behavior with hidden text changed in KiCad 8.0.2, it
   is computed even for operations where it isn’t really visible, like
   plotting a layer where we don’t have the hidden text. So currently
   KiBot is experimentally disabling the “hidden text layer”. This is a
   bug in KiCad (https://gitlab.com/kicad/code/kicad/-/issues/17958)
-  Render 3D: Modern versions of Image Magick no longer needs two trim
   passes for auto-crop, so now we default to one and an option enables
   two. (See #644)
-  Preflights: The definition of preflight plug-ins changed. They are
   slightly different now. Currently they are Optionable and share more
   in common with outputs. If you need assistance to migrate a preflight
   just open a GitHub issue.
-  Outputs: Now all options must declare its default.
-  Global ``invalidate_pcb_text_cache``: now it changes the PCB on disk,
   not just on memory. This is needed for external tools like KiKit’s
   panelize.
-  In many cases now we allow empty lists and use some sort of default.
   A warning is issued, but we continue.

   -  Layers: now the default for missing layers is all layers.
   -  Copy files: Now we don’t stop when nothing to copy is specified
   -  Layers: now the default for missing layers is all layers.
   -  KiKit Present: Missing description is no longer fatal
   -  Any PCB Print/PCB Print: Missing pages/layers is no longer fatal
   -  Populate: Missing input file is no longer fatal
   -  QR Lib: Missing QR definition is no longer fatal (%p %r used)
   -  Blender Options outputs: Make a render when no outputs are
      specified
   -  PCB Print: repeat_layers defaults to inners
   -  Spec to Field: some simple defaults for the specs (voltage,
      current, power and tolerance)

.. _section-8:

`1.7.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.6.5...v1.7.0>`__ - 2024-04-23
-----------------------------------------------------------------------------------

.. _added-8:

Added
~~~~~

-  New preflights:

   -  erc: a replacement for run_erc when using KiCad 8. It can generate
      ERC reports not only in plain text but also HTML, JSON and CSV.
   -  drc: a replacement for run_drc when using KiCad 8. Also supporting
      multiple formats and with a modern separation between unconnected
      and warnings.
   -  update_footprint: updates one or more footprints from the libs.
      Useful for external QR codes, logos, etc. (#492 #483)
   -  draw_stackup: creates a nice drawing for the stackup (See #368)
   -  update_pcb_characteristics: updates the text you get from *Place*
      -> *Add Board Characteristics*, so you don’t need to remove it and
      place again. (See #384 #368)
   -  update_stackup: updates the text you get from *Place* -> *Add
      Stackup Table*, so you don’t need to remove it and place again.
      (See #384 #368)

-  Global variables:

   -  str_yes/str_no: to finetune the *update_pcb_characteristics*
      preflight.

-  Internal templates:

   -  ExportProject: creates a ZIP file containing a self-contained
      version of the project. All footprint, symbols and 3D models are
      included.

-  Filters:

   -  Now the *var_rename* and *var_rename_kicost* filters can be used
      to change footprints using variants (See #574)

-  Quick Start: D/ERC are also included for KiCad 8 (with dont_stop:
   true)
-  Navigate Results: Includes the new D/ERC
-  SCH Print:

   -  Option to specify a custom page layout (WKS)
   -  Workaround for people using backslashes (i.e. Windows+WSL) (See
      #607)

-  PCB Print:

   -  Support for (undocumented) KiCad 8.0 worksheets (20231118) (See
      #607)
   -  Control over the LAYER KiCad variable used in worksheets
      (layer_var ops)

-  Internal BoM:

   -  Colored rows for HTML and XLSX (See #344)

-  Render 3D:

   -  Added options to control Eco1/Eco2/Drawings individually on KiCad
      8 (#614)

.. _fixed-9:

Fixed
~~~~~

-  Netlist generation problems with components on the PCB but not in
   schematic. I.e. logos reaching iBoM output (#598)
-  3D/2D renderers: ranges regex to be more strict. Don’t take things
   like “r1-10”
-  Sch errors are now caught during output runs. (#604)
-  Compress:

   -  Could make Python ZIP lib crash when adding a dir to the zip root.
   -  So it also removes subdirs created by an output when using move.

-  Copy Files:

   -  Problems when no target dir and no WKS.
   -  Problems when finding the targets (Makefile, copy files, etc.)
      before generating the outputs (or when moved).

-  BoM:

   -  Expansion of variables in fields could fail if the KiCad config
      wasn’t initialized

.. _changed-7:

Changed
~~~~~~~

-  Filters: When we find a component in the PCB, that is not in the
   schematic, and has a malformed reference, now we inform a warning,
   discard the component and continue. (#604)
-  PcbDraw: Now handles panelized boards much faster. Previous code was
   really slow for panels and the time increased exponentially.

.. _section-9:

`1.6.5 <https://github.com/INTI-CMNB/KiBot/compare/v1.6.4...v1.6.5>`__ - 2024-03-31
-----------------------------------------------------------------------------------

.. _added-9:

Added
~~~~~

-  KiCad 8 support
-  Panelize: support for all new options (upto 1.5.1)
-  3D/2D renderers: support for ranges in the ``show_components`` and
   ``highlight`` options. So one entry can be something like *R10-R20*.
   Can be disabled using the global option ``allow_component_ranges``.
   (See yaqwsx/PcbDraw#159)
-  Navigate results: A header and navigation bar (#582)
-  BoM: support for SVG format in the logos (#383)

.. _changed-8:

Changed
~~~~~~~

-  CI/CD: we now filter some warnings that are always generated by
   docker images when we detect a CI/CD environment. They can be enabled
   using the ``--warn-ci-cd`` command line option. (See #564)
-  KiRi: continue even on corrupted schematics (#583)
-  Variants: avoid W045 on nameless pads. Assuming they are on purpose
   and not real pads. (See #584)
-  BoardView: Skip footprints with no pads (not just REF*\*)
   (whitequark/kicad-boardview#14)

.. _fixed-10:

Fixed
~~~~~

-  Netlist generation problems with components on the PCB but not in
   schematic. (#578)
-  Filters:

   -  \_none filter not always honored (i.e. exclude in BoM) (#580)
   -  Rotation for bottom JLCPCB parts with offset (#591)
   -  Rotation angle used to compute the offsets, must be the final
      angle

-  PCB Parity: components excluded from the board reported anyways
   (#585)
-  BoardView:

   -  X axis mirroring issues (whitequark/kicad-boardview#11)
   -  Alphanumeric pads sorting (whitequark/kicad-boardview#17) and
      (whitequark/kicad-boardview#18)

-  Present: problems when using gerbers already generated
-  Diff: problems when using things like “origin/main” and add_link_id
   (#589)
-  Panelize: not able to use external JSON configs (#592)

.. _section-10:

`1.6.4 <https://github.com/INTI-CMNB/KiBot/compare/v1.6.3...v1.6.4>`__ - 2024-02-02
-----------------------------------------------------------------------------------

.. _added-10:

Added
~~~~~

-  New outputs:

   -  KiRi: interactive diff
   -  KiCanvas: on-line schematic/PCB browser

-  General:

   -  Operations that copies the project now also copies the PRL and the
      DRU
   -  Files named \*.kibot.yml are also detected as configuration files
   -  Mechanism to specify

      -  All inner layers (inners)
      -  All external copper layers (outers)

-  Command line:

   -  ``--help-list-offsets`` to list footprint offsets (JLCPCB)
   -  ``--help-list-rotations`` to list footprint rotations (JLCPCB)
   -  ``--stop-on-warnings`` (``-W``) to stop on warnings (#545)
   -  ``--defs-from-env`` allows using environment vars for substitution
      (#549)

-  Global options:

   -  ``remove_solder_mask_for_dnp`` similar to
      ``remove_solder_paste_for_dnp`` but applied to the solder mask
      apertures. (#476)
   -  ``layer_defaults`` to specify the default suffix and description.
      (#504)
   -  ``include_components_from_pcb`` to disable the new behavior that
      includes components from the PCB in the filter/variants processing
   -  ``restore_project`` now also restores the PRL

-  Schematic format:

   -  Support for *unit names* (#513)

-  Internal templates:

   -  3DRender_top, 3DRender_top_straight, 3DRender_bottom and
      3DRender_bottom_straight: to generate simple and quick 3D renders.
   -  \_KIBOT_POS_DNF_FILTER option to JLCPCB. It now excludes
      components added by KiKit to create panels and can be customized.
   -  \_KIBOT_PLOT_FOOTPRINT_REFS and \_KIBOT_PLOT_FOOTPRINT_VALUES to
      manufacturer templates. (#523)
   -  \_KIBOT_COMPRESS_MOVE to move gerber and drill files to the
      compressed output, enabled by default. (#537)

-  Filters:

   -  New ``_rot_footprint_jlcpcb`` internal filter to fix the JLCPCB
      bottom rotations.
   -  New options for the ``rot_footprint`` filters: (See #510)

      -  ``mirror_bottom``: used to undo the KiCad mirroring of the
         bottom.
      -  ``rot_fields``: list of fields to indicate arbitrary rotations.
      -  ``offset_fields``: list of fields to indicate arbitrary
         offsets.
      -  ``offsets``: a list of pairs containing regex and offset (“x,
         y”)
      -  ``bennymeg_mode``: used to provide compatibility with the
         bennymeg/JLC-Plugin-for-KiCad tool.
      -  ``rotations_and_offsets``: a more flexible mechanism to select
         rotations and offsets. So you can have two different rotations
         applied to the same footprint, i.e. different components with
         the same footprint but different orientation in the reel.

-  3D outputs:

   -  ``download_lcsc`` option to disable LCSC 3D model download (See
      #415)

-  Preflights:

   -  Individual directory for the ERC and DRC reports (#562)

-  BoM:

   -  Support for ${field} expansion. (#471)
   -  LCSC links (SchrodingersGat/KiBoM#190)
   -  ``parse_value`` can be used to disable the *Value* parser (See
      #494) Also added a warning about using extra data in the *Value*
      field.

-  iBoM:

   -  ``forced_name`` option to force the name displayed at the top left
      corner (#470)

-  Blender export:

   -  Support for pcb2blender v2.6/2.7 (Blender 3.5.1/3.6)
   -  ``auto_camera_z_axis_factor``: used to control the default camera
      distance
   -  Options to create simple animations:

      -  PoV ``steps``: to create rotation angle increments
      -  ``default_file_id``: can be used to create numbered PNGs
      -  ``fixed_auto_camera``: to avoid adjusting the automatic camera
         on each frame

   -  Camera option to set the clip start (#484)
   -  Traceback dump when Blender output contains it
   -  Subdirectory for each output generated (#541)
   -  Option to disable the denoiser (#539)

-  KiKit

   -  Expand text variables and KiBot %X markers in text objects (see
      #497)

-  PCB Print:

   -  Support for CURRENT_DATE text variable
   -  Options to mirror the text in the user layers when creating a
      mirrored page (#561)
   -  Options to select which layers are used for centering purposes
      (#573)

-  Populate:

   -  Basic support for regular list items (#480)

-  Position:

   -  Experimental support for gerber position files (#500)

-  Copy Files:

   -  Mode to export the whole project (SCH, PCB, symbols, footprints,
      3D models and project files) (#491)

-  Help for the error levels
-  Warnings:

   -  Explain about wrong dir/output separation (#493)

-  Diff:

   -  Added option to un/fill zones before doing the comparison (See
      #391)
   -  Added a new mode where we can control the added/removed colors
      (#551)

.. _changed-9:

Changed
~~~~~~~

-  Documentation:

   -  Now you can search in the docs
   -  Indexed so you can search by topic
   -  With a navigation side bar

-  Variants and filters:

   -  Components only in the PCB are now processed

-  QR Lib:

   -  Footprints: now they are flagged with exclude from BoM and Pos,
      also with no court yard requirements for KiCad 7
   -  Symbol: Excluded from simulation for KiCad 7

-  Elecrow, FusionPCB, JLCPCB, PCBWay and P-Ban templates now moves the
   files to the compressed output by default.

   -  Note that JLCPCB BoM and Position files aren’t included anymore,
      they are uploaded separately.

-  Quick Start:

   -  Now we generate only for projects, not separated files. This
      avoids problems for sub-sheets in separated dirs.

-  Diff:

   -  When *check_zone_fills* is enabled now we do a refill for the
      boards

.. _fixed-11:

Fixed
~~~~~

-  Schematics:

   -  Problems with deep nested and recycled sheets (#520)
   -  Problems saving deep nested sheets
   -  Makefile/compress targets

-  Rotated polygons and text used in the worksheet (#466)
-  The –log/-L didn’t enabled full debug for all messages
-  BoM:

   -  Problems when trying to aggregate the datasheet field (#472)

-  kibot-check:

   -  Show 7.x as supported (#469)

-  Blender export:

   -  Rotations are now applied to the current view, not just the top
      view
   -  Board/components not visible for small boards (See #484)
   -  Light type names (extra space) (#505)
   -  Problems when no point of view was defined (#546)

-  update_xml with check_pcb_parity enabled:

   -  Avoid errors for KiCad 6 using “Exclude from BoM” components. This
      limitation isn’t found on KiCad 7. (#486)
   -  *exclude_from_bom* mismatch on KiCad 7
   -  *Sheetfile* mismatch on KiCad 7 when testing from different
      directory
   -  Honor the ‘Not in schematic’ (board_only) flag when doing a parity
      check

-  Dependencies downloader:

   -  Problems when connection timed-out

-  Sub PCB separation using annotation method for some edeges and KiCad
   versions (#496)
-  Problems when using NET_NAME(n) for a value (#511)
-  JLCPCB rotations for bottom components
-  Copy Files:

   -  Warnings when using both, the STEP and WRL model, of the same
      component
   -  Fail to detect 3D models subdirs when running alone

-  QR Lib:

   -  When used from the preflight the name of the file changed to the
      name of a temporal, generating problems with the plot outputs,
      like pcb_print
   -  Project options not preserved, i.e. set_text_variables failing
   -  Bottom QRs should be mirrored in the Y axis

-  Diff

   -  ``current``: didn’t apply global variants
   -  ``current``: didn’t honor KiCad native DNP flags, they need a
      filter
   -  Problems when trying to use an already existent worktree (#555)
   -  Avoid using unexpected branches for worktrees (#556)

-  PCB Print:

   -  Issues when forcing the board edge and using scaling (#532)
   -  Text not searchable when using newer rsvg-convert tools (#552)

-  Quick Start:

   -  Problems with KiCad 6+ files using KiCad 5 names for layers
   -  Problems scanning dirs without enough privileges

-  PCB/SCH Variant

   -  Makefile/compress targets (missing project)

-  3D outputs:

   -  Problems when creating a colored resistor, but we didn’t have a
      cache yet (i.e. no model downloaded) #553

.. _section-11:

`1.6.3 <https://github.com/INTI-CMNB/KiBot/compare/v1.6.2...v1.6.3>`__ - 2023-06-26
-----------------------------------------------------------------------------------

.. _added-11:

Added
~~~~~

-  General:

   -  OS environment expansion in ${VAR}
   -  Now outputs can request to be added to one or more groups (#435)
   -  PCB text variables cached in the PCB are now reset when the config
      uses ``set_text_variables``. This is a complex dilemma of KiCad
      6/7 policy implementation. See `KiCad issue
      14360 <https://gitlab.com/kicad/code/kicad/-/issues/14360>`__.
      (#441)
   -  Default values for @TAGS@
   -  Parametrizable imports

-  Command line:

   -  ``--list-variants`` List all available variants (See #434)
   -  ``--only-names`` to make ``--list`` list only output names
   -  ``--only-pre`` to list only the preflights
   -  ``--only-groups`` to list only the groups
   -  ``--output-name-first`` to list outputs by name, no description
      (See #436)

-  Global options:

   -  ``use_os_env_for_expand`` to disable OS environment expansion
   -  ``environment``.\ ``extra_os`` to define environment variables
   -  ``field_voltage`` Name/s of the field/s used for the voltage
      raiting
   -  ``field_package`` Name/s of the field/s used for the package, not
      footprint
   -  ``field_temp_coef`` Name/s of the field/s used for the temperature
      coefficient
   -  ``field_power`` Name/s of the field/s used for the power raiting
   -  ``invalidate_pcb_text_cache`` controls if we reset the text
      variables cached in the PCB file.
   -  ``git_diff_strategy`` selects how we preserve the current repo
      state. (See #443)

-  Filters:

   -  New ``value_split`` to extract information from the Value field
      and put it in separated fields. I.e. tolerance, voltage, etc.
   -  New ``spec_to_field`` to extract information from the distributors
      specs and put in fields. I.e. RoHS status.
   -  New ``generic`` options ``exclude_not_in_bom`` and
      ``exclude_not_on_board`` to use KiCad 6+ flags. (See #429)

-  Internal templates:

   -  JLCPCB_with_THT and JLCPCB_stencil_with_THT: adding THT
      components.

-  New internal filters:

   -  ``_value_split`` splits the Value field but the field remains and
      the extra data is not visible
   -  ``_value_split_replace`` splits the Value field and replaces it

-  Internal templates:

   -  CheckZoneFill: Used to check if a zone fill operation makes the
      PCB quite different (#431)
   -  Versions with stencil for Elecrow, FusionPCB, P-Ban and PCBWay.
   -  PanelDemo_4x4: Demo for a 4x4 panel.

-  Render_3D:

   -  ``realistic``: can be used to disable the realistic colors and get
      the GUI ones
   -  ``show_board_body``: can be used to make the PCB core transparent
      (see inner)
   -  ``show_comments``: to see the content of the User.Comments layer.
   -  ``show_eco``: to see the content of the Eco1.User/Eco2.User
      layers.
   -  ``show_adhesive``: to see the content of the \*.Adhesive layers.

-  Navigate_Results:

   -  ``skip_not_run``: used to skip outputs not generated in default
      runs.

-  Compress:

   -  ``skip_not_run``: used to skip outputs not generated in default
      runs.

-  Position:

   -  ``quote_all``: forces quotes to all values in the CSV output. (See
      #456)

.. _changed-10:

Changed
~~~~~~~

-  Command line:

   -  ``--list`` also lists groups

-  KiCad v6/7 schematic:

   -  When saving an schematic the hierarchy is expanded only if needed,
      i.e. value of an instance changed

-  List actions:

   -  Now you must explicitly ask to configure outputs. Otherwise isn’t
      needed. As a result you no longer need to have an SCH/PCB. Use
      ``--config-outs`` to get the old behavior.

-  Git diff link file name:

   -  Now we default to using worktrees instead of stash push/pop. As a
      side effect the names of the git points are changed. This is
      because main/master only applies to the main worktree. So the
      names now refer to the closest tag.

-  JLCPCB_stencil: Is now just like JLCPCB. The only difference is the
   added layers.

.. _fixed-12:

Fixed
~~~~~

-  KiCad v6/7 schematic:

   -  Net Class Flags not saved in variants or annotated schematics
   -  Repeated UUIDs saved in variants
   -  Bitmap scale not saved in variants or annotated schematics
   -  ``lib_name`` attribute not saved in variants or annotated
      schematics

-  Position:

   -  Components marked as “Exclude from position files” not excluded
      when only SMD components are selected. (See #429)

-  Diff:

   -  KIBOT_TAG with n > 0 skipped n commits, not n tags (#430)
   -  Details related to the project not applied during a diff involving
      a variant (project not copied) (#438)

-  Copy files:

   -  PCB not loaded if the only action was to copy the 3D models
   -  Problems for STEP models when copying models

-  Gerber:

   -  Problems trying to compress gerbers for a board with inner layers
      when using legacy file extensions (#446)

-  Electro-grammar:

   -  Problems with floating point tolerances (i.e. 0.1%) (#447)

-  KiCad user template directory autodetection for KiCad 7+

.. _section-12:

`1.6.2 <https://github.com/INTI-CMNB/KiBot/compare/v1.6.1...v1.6.2>`__ - 2023-04-24
-----------------------------------------------------------------------------------

.. _added-12:

Added
~~~~~

-  General:

   -  Support for time stamp in the date (i.e. 2023-04-02T09:22-03:00)
   -  Support to pass variables to the 3D models download URL (#414)
   -  Support for netclass flags (#418)
   -  Export *KICADn\_* environment variables for the older versions So
      you can use *KICAD6\_* variables on KiCad 7.

-  Expansion patterns:

   -  **%M** directory where the pcb/sch resides. Only the last
      component i.e. /a/b/c/name.kicad_pcb -> c (#421)

-  Command line:

   -  ``--banner N`` Option to display a banner
   -  ``--log FILE`` Option to log to a file, in addition to the stderr

-  Global options:

   -  ``colored_tht_resistors`` to disable the 3D colored resistors.
   -  ``field_tolerance`` field/s to look for resistor tolerance.
   -  ``default_resistor_tolerance`` which tolerance to use when none
      found.
   -  ``cache_3d_resistors`` to avoid generating them all the time.
   -  ``resources_dir`` to specify fonts and colors to install (CI/CD)

-  3D: colored 3D models for THT resistors
-  Blender export:

   -  Better default light
   -  More light options

-  Datasheet download: now the warnings mention which reference failed.
-  Plot related outputs and PCB_Print:

   -  ``individual_page_scaling``: to control if the center of the page
      is computed using all pages or individually.

-  Plot related outputs:

   -  All outputs now support scaling.

-  BoM:

   -  Support for extra information in the *Value* field. Currently just
      parsed, not rejected.

-  PCB/SCH parity test:

   -  Check for value and fields/properties.

-  SCH print:

   -  Support for title change

-  VRML:

   -  Option to use the auxiliary origin as reference. (#420)

.. _fixed-13:

Fixed
~~~~~

-  Makefile: don’t skip all preflights on each run, just the ones we
   generate as targets. (#405)
-  KiKit present: problems when no board was specified. (#402)
-  Datasheet download:

   -  Avoid interruptions when too many redirections is detected (#408)

-  PcbDraw:

   -  KiCad 7.0.1 polygons used as board edge. (yaqwsx/PcbDraw#142)

-  PCB Print:

   -  Interference between the visible layers in the PRL file and the
      results when scaling. (#407)
   -  Problems with images in the WKS (KiCad 5/6)

-  Diff:

   -  Problems when using an output and no variant specified.

-  PCB/SCH parity test:

   -  Workaround for bogus net codes generated by KiCad (#410)

-  3D Models:

   -  Problems to download KiCad 7 models (#417)
   -  Added workaround for KiCad 7 failing to export VRMLs for PCBs
      using paths relative to the footprint. (See #417)

-  VRML:

   -  ref_y coordinate not used. (#419)

.. _changed-11:

Changed:
~~~~~~~~

-  Some R, L and C values that were rejected are accepted now. You just
   get a warning about what part of the value was discarded.

.. _section-13:

`1.6.1 <https://github.com/INTI-CMNB/KiBot/compare/v1.6.0...v1.6.1>`__ - 2023-03-16
-----------------------------------------------------------------------------------

.. _added-13:

Added
~~~~~

-  KiCad 7.0.1 support
-  Global options:

   -  ``allow_blind_buried_vias`` and ``allow_microvias`` for KiCad 7
      (no longer in KiCad)
   -  ``erc_grid`` to specify the grid size for KiCad 7 ERC tests

-  Report:

   -  Counters for total vias and by via type (``vias_count``,
      ``thru_vias_count``, ``blind_vias_count`` and
      ``micro_vias_count``)
   -  Warnings when micro and/or blind vias aren’t allowed, but we found
      them.

-  KiCad 7 specific:

   -  Avoid warnings about missing coutyard for footprints marked as
      excluded from courtyard tests.
   -  ``kicad_dnp_applied`` global option to use the *Do Not Populate*
      schematic flag as *do not fit* for KiBot, enabled by default.
   -  ``kicad_dnp_applies_to_3D`` global option to eliminate the 3D
      models of components marked as *Do Not Populate*. This option
      applies to the case where no filter or variants are in use.
      Enabled by default. The ``kicad_dnp_applied`` option also disables
      it.
   -  ``cross_using_kicad`` global option to use KiCad to cross DNP
      components in the schematic. Enabled by default.

.. _fixed-14:

Fixed
~~~~~

-  Problems to detect the schematic name when the path to the config
   contained a dot that isn’t used for an extension and some particular
   conditions were met.
-  PCB Print: KiCad crashing on some complex filled zones (#396)

.. _section-14:

`1.6.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.5.1...v1.6.0>`__ - 2023-02-06
-----------------------------------------------------------------------------------

.. _added-14:

Added
~~~~~

-  General:

   -  Support for ``groups`` of ``outputs``
   -  Internal templates import
   -  Better support for wrong pre-flight options (#360)
   -  A mechanism to cache downloaded 3D models
   -  Support to download 3D models from EasyEDA (using LCSC codes)

-  Global options:

   -  field_lcsc_part: to select the LCSC/JLCPCB part field

-  New outputs:

   -  ``vrml`` export the 3D model in Virtual Reality Modeling Language
      (#349)
   -  ``ps_sch_print``, ``dxf_sch_print`` and ``hpgl_sch_print``
      variants of ``pdf_sch_print``
   -  ``blender_export`` exports the PCB to Blender and other 3D
      formats, renders the PCB with impressive quality (experimental)

-  New internal filters:

   -  ``_only_smd`` used to get only SMD parts
   -  ``_only_tht`` used to get only THT parts
   -  ``_only_virtual`` used to get only virtual parts

-  Variants:

   -  Support for multi-boards as defined by KiKit

-  Internal templates:

   -  FusionPCB: gerber, drill and compress
   -  Elecrow: gerber, drill and compress
   -  JLCPCB: gerber, drill, position, BoM and compress
   -  MacroFab_XYRS: XYRS position file compatible with MacroFab
   -  P-Ban: gerber, drill and compress
   -  PCB2Blender_2_1: generates a pcb2blender 2.1 file to import on
      Blender (See #349)
   -  PCB2Blender_2_1_haschtl: PCB2Blender_2_1 variant for @Haschtl
      fork.
   -  PCBWay: gerber, drill and compress

-  Compress:

   -  Option to use the output’s ``dir`` as reference
      (``from_output_dir``)

-  iBoM:

   -  ``hide_excluded`` to hide excluded \*.Fab drawings.

-  PCB_Print:

   -  Added a mechanism to create a page for each copper layer. (#365)

-  Plot related outputs and PCB_Print:

   -  Added support for the KiCad 6 “sketch_pads_on_fab_layers” option.
      (#356)

-  Report:

   -  Expansion for KiCad text variables and environment variables (See
      #368)

-  \*SCH_Print:

   -  Added options to select the color theme and enable background
      color. (#362)

-  SVG:

   -  Options to limit the view box to the used area. ### Fixed

-  BoM:

   -  pre_transform filers can’t be logic filters

-  Copy_Files:

   -  Problems on KiCad 5 (no 3rd party dir) (#357)
   -  Problems with compress output (also Makefile) (#372)

-  DOCs

   -  annotate_pcb pre-flight missing options (#360)
   -  annotate_pcb pre-flight wrong example (#360)

-  iBoM:

   -  Variant changes to the \*.Fab weren’t exported. Now all 2D variant
      stuff is applied before calling iBoM (#350)

-  PCB_Print:

   -  Images not showing in custom frames. (#352)
   -  Problems when trying to use groups of layers (i.e. copper)

-  Report:

   -  Computed size when using circles and some arcs in the PCB edge
      (#375) ### Changed

-  Downloaded 3D models are no longer discarded. They are stored in
   ~/.cache/kibot/3d You can change the directory using KIBOT_3D_MODELS
-  License is now AGPL v3, since we are incorporating AGPL code.

.. _section-15:

`1.5.1 <https://github.com/INTI-CMNB/KiBot/compare/v1.5.0...v1.5.1>`__ - 2022-12-16
-----------------------------------------------------------------------------------

.. _fixed-15:

Fixed
~~~~~

-  System level resources look-up

.. _section-16:

`1.5.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.4.0...v1.5.0>`__ - 2022-12-16
-----------------------------------------------------------------------------------

.. _added-15:

Added
~~~~~

-  New output:

   -  ``populate`` to create step-by-step assembly instructions With
      support for ``pcbdraw`` and ``render_3d``.
   -  ``panelize`` to create a PCB panel containing N copies of the PCB.
   -  ``stencil_3d`` to create 3D self-registering printable stencils.
   -  ``stencil_for_jig`` to create steel stencils and 3D register.
   -  ``kikit_present`` to create a project presentation web page.

-  generic filters: options to filter by PCB side
-  BoM:

   -  Option to link to Mouser site.
   -  Human readable text output format.

-  Diff:

   -  Option to compare only the first schematic page. (See #319)

-  iBoM:

   -  Support for the ``offset_back_rotation`` option

-  Navigate Results:

   -  Support for compress

-  PcbDraw:

   -  BMP output format
   -  Image margin
   -  Outline width
   -  Solder paste removal
   -  V-CUTS layer
   -  Resistor remap and flip
   -  A ``remap_components`` option with better type checks
   -  Better support for variants
   -  Option to control the *SVG precision* (units scale)
   -  Filter expansion in ``show_components`` and ``highlight``

-  PCB_Print:

   -  Option to control the *SVG precision* (units scale)
   -  Now the text in the PDF is searchable. (#331)
   -  Margins for the autoscale mode. (#337)

-  Render_3D:

   -  Option to render only some components (like in PcbDraw)
   -  Option to auto-crop the resulting PNG
   -  Option to make transparent the background
   -  Option to highlight components

-  SVG:

   -  Option to control the *SVG precision* (units scale)

.. _changed-12:

Changed
~~~~~~~

-  Diff:

   -  Now the default is to compare all the schematic pages. (#319)

-  Report:

   -  loss tangent decimals, added one more.

.. _fixed-16:

Fixed
~~~~~

-  QR lib update: Problems when moving the footprint to the bottom for
   KiCad 5.
-  SVG, PCB_Print, PcbDraw: Problems to display the outputs using Chrome
   and Firefox.
-  Diff: Problems when comparing to a repo point where the PCB/SCH
   didn’t exist yet. (#323)
-  Report: Problems when using NPTH holes with sizes that doesn’t
   correspond to real drill tools. It generated bogus reports about
   wrong OARs. (#326)
-  Problems when using more than one dielectric in the stack-up. (#328)
-  Gerber: Extension used for JLCPCB inner layers. (#329)
-  BoM:

   -  The length of the CSV separator is now validated.
   -  Using the escaped t, n, r and  is now supported. (See #334)
   -  Digi-key link in the HTML output.

-  KiBoM: User defined fields wasn’t available as column names. (#344)
-  Imports:

   -  Problems with recursive imports when the intermediate import
      didn’t contain any of the requested elements (i.e. no outputs).
      (#335)

-  Navigate results: fail when no output to generate. Now you get a
   warning.
-  Makefile: outputs marked as not run by default were listed in the
   ``all`` target.

.. _section-17:

`1.4.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.3.0...v1.4.0>`__ - 2022-10-12
-----------------------------------------------------------------------------------

.. _added-16:

Added
~~~~~

-  General things:

   -  Some basic preprocessing, now you can parametrize the YAML config.
      (See #233 #243)
   -  Support for 3D models aliases and also a global option to define
      them in the KiBot configuration (See #261)
   -  Environment and text variables now can be used as 3D model
      aliases. (See #261)
   -  Environment and text variables expansion is now recursive. So in
      ``${VAR}`` the *VAR* can contain ``${OTHER_VAR}``
   -  Command line option to specify warnings to be excluded. Useful for
      warnings issued before applying the global options (i.e during
      import). (#296)
   -  ``pre_transform`` filter to outputs supporting variants.

-  New outputs:

   -  PCB_Variant: saves a PCB with filters and variants applied.
   -  Copy_Files: used to copy files to the output directory. (#279) You
      can also copy the 3D models.

-  Support for Eurocircuits drill adjust to fix small OARs. Option
   ``eurocircuits_reduce_holes``. (#227)
-  Global options:

   -  Support for changing text variables with variants during outputs
      creation. Option ``set_text_variables_before_output``. (See #233)
   -  Options to control which stuff is changed on PCB variants: (See
      #270)

      -  cross_footprints_for_dnp
      -  remove_adhesive_for_dnp
      -  remove_solder_paste_for_dnp
      -  hide_excluded (default value)

   -  Mechanism to give more priority to local globals. (See #291)

-  Diff:

   -  Mechanism to compare using a variant (See #278)
   -  Mechanism to specify the current PCB/Schematic in memory (See
      #295)
   -  Mechanism to compare with the last Nth tag (See #312)
   -  Option to skip pages with no differences

-  Sch Variant:

   -  Option to copy the project. Needed for text variables.
   -  Option to change the title (similar to PCB Variant)

-  Render_3D: Options to disable some technical layers and control the
   silkscreen clipping. (#282)
-  Internal BoM:

   -  Now you can aggregate components using CSV files. (See #248)
   -  Added some basic support for “Exclude from BoM” flag (See #316)

-  Now you can check PCB and schematic parity using the ``update_xml``
   preflight (See #297)
-  New filters:

   -  ``urlify`` to convert URLs in fields to HTML links (#311)
   -  ``field_modify`` a more generic field transformer

-  Position: option to set the resolution for floating values (#314)

.. _fixed-17:

Fixed
~~~~~

-  Problems to compress netlists. (#287)
-  2D PCB processing didn’t show in 3D targets (i.e. solder paste not
   removed in the 3D render). (See #270)
-  KiBot exited when downloading a datasheet and got a connection error
   (#289 #290)
-  KiCad 5 “assert”lower <= upper” failed in Clamp()” (#304)
-  Missing XYRS information for components with multiple units (#306)
-  Schematic v6:

   -  Problems when creating a variant of a sub-sheet that was edited as
      a standalone sheet (#307)
   -  Autoplace fields could be lost in variants.

-  iBoM: Name displayed in the HTML when using filters and/or variants.
-  Position: Components wrongly separated by side when the side column
   wasn’t the last column (#313)

.. _changed-13:

Changed
~~~~~~~

-  Diff:

   -  When comparing a file now the links says Current/FILE instead of
      None
   -  The default was to compare the current file on storage, now is the
      current file on memory. It includes the zone refill indicated in
      the preflights. (See #295)
   -  Now the error about differences bigger than the threshold is more
      clear. KiBot also returns a distinct error level.

-  Now the global ``dir`` option also applies to the preflights, can be
   disabled using ``use_dir_for_preflights``. (#292)
-  When importing globals now options that are lists or dicts are
   merged, not just replaced. (#291)

.. _section-18:

`1.3.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.2.0...v1.3.0>`__ - 2022-09-08
-----------------------------------------------------------------------------------

.. _added-17:

Added
~~~~~

-  New outputs:

   -  Diff: to compute differences between PCBs and SCHs.
      (INTI-CMNB/KiAuto#14)
   -  Info: collects info about the environment. (See #209)

-  Try to download missing tools and Python modules. The user also gets
   more information when something is missing. It can be disabled from
   the command line.
-  Global options:

   -  Cross components without a body (#219)
   -  Restore the project at exit (#250)

-  Imports:

   -  Now you can nest imports (import from an imported file) (#218)
   -  Preflights can be imported (#181)

-  ``--dont-stop`` command line option, to try to continue even on
   errors (#209)
-  PDF/SVG PCB Print: option to print all pages/single page (#236)
-  iBoM: Support for variants that change component fields (#242)
-  Workaround for problems with DRC exclusions (See INTI-CMNB/KiAuto#26,
   #250) Global option: ``drc_exclusions_workaround`` KiCad bug
   `11562 <https://gitlab.com/kicad/code/kicad/-/issues/11562>`__
-  Internal BoM: KiCad 6 text variables expansion in the fields (#247)
-  Compress: Option to store symlinks. (See #265)
-  PCB Print:

   -  Option to configure the forced edge color. (#281)
   -  Option to control the resolution (DPI). (See #259)
   -  Option to move the page number to the extension
      (page_number_as_extension) (See #283)
   -  Option to customize the page numbers (See #283)

-  Installation checker: option to show the tool paths.

.. _fixed-18:

Fixed
~~~~~

-  OAR computation (Report) (#225)
-  Position: Problems when doing manual panelization (repeated
   references) (#224)
-  PCB_Print:

   -  Problems with filtered/modified PCBs
   -  Problems with zones on multiple layers (#226)
   -  Problems with ``hide_excluded: true`` and components not in the
      SCH (#258)
   -  Text vars generated in the same run didn’t show up (#280)
   -  Low resolution for the solder mask. (See #259)

-  SCH Variants on KiCad 6: Problems with missing values in the title
   block.
-  Report: Converted file wasn’t stored at ``dir`` (#238)
-  Datasheet download: Time-outs on some servers expecting modern
   browsers (#240)
-  SCH Print and Netlist: name collisions. When the default name used by
   KiCad belongs to an already existing file. (#244)
-  Install checker: fixed problems to detect iBoM installed as plugin.
   (#209)
-  Internal Netlist generation (i.e. iBoM with variants): problems withg
   components that doesn’t specify a library. (See #242)
-  Problems when setting a text variable to an empty string. (#268)
-  QR lib update: Problems when moving the footprint to the bottom.
   (#271)
-  Misleading messages for missing 3D models that starts with ${VAR}
   when VAR isn’t defined. The old code tried to make it an absolute
   path.

.. _changed-14:

Changed
~~~~~~~

-  The order in which main sections are parsed is now fixed. The
   declared order is ignored. The order is: kiplot/kibot, import,
   global, filters, variants, preflight, outputs
-  Datasheet download:

   -  Continue downloading if an SSL certificate error found (#239)

-  PCB_Print: PNGs no longer has transparent background. This is because
   now we use a PDF as intermediate step.
-  Fails to expand KiCad vars are reported once (not every time)
-  No more warnings about missing 3D models when we can download them

.. _section-19:

`1.2.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.1.0...v1.2.0>`__ - 2022-06-15
-----------------------------------------------------------------------------------

.. _added-18:

Added
~~~~~

-  The outputs help now display the more relevant options first and
   highlighted. Which ones are more relevant is somehow arbitrary,
   comments are welcome.
-  General stuff:

   -  Outputs now can have priorities, by default is applied. Use ``-n``
      to disable it.

-  New outputs:

   -  ``navigate_results`` creates web pages to browse the generated
      outputs.
      `Example <https://inti-cmnb.github.io/kibot_variants_arduprog_site/Browse/t1-navigate.html>`__

-  New globals:

   -  ``environment`` section allows defining KiCad environment
      variables. (See INTI-CMNB/KiAuto#21)

-  GitHub discussions are now enabled. Comment about your KiBot
   experience `here <https://github.com/INTI-CMNB/KiBot/discussions>`__

.. _fixed-19:

Fixed
~~~~~

-  Components with mounting hole where excluded (#201)
-  GenCAD output targets.
-  Problems expanding multiple KiCad variables in the same value.
-  XML BoM: Fixed problems with fields containing / (#206)
-  pcb_print: vias processing was disabled.
-  pcb_print: problems with frame in GUI mode and portrait page
   orientation.
-  svg_pcb_print: page orientation for portrait.

.. _changed-15:

Changed
~~~~~~~

-  KiCad environment variables: more variables detected, native KiCad 6
   names, all exported to the environment (#205)
-  Consequences of the priorities implementation:

   -  ``qr_lib`` outputs are created before others
   -  ``navigate_results`` and ``compress`` outputs are created after
      others

.. _section-20:

`1.1.0 <https://github.com/INTI-CMNB/KiBot/compare/v1.0.0...v1.1.0>`__ - 2022-05-24
-----------------------------------------------------------------------------------

.. _added-19:

Added
~~~~~

-  ``kibot-check`` tool to check the installation
-  New outputs:

   -  KiCad netlist generation
   -  IPC-D-356 netlist generation (#197)

-  Internal BoM:

   -  Pattern and text variables expansion in the title (#198)
   -  Customizable extra info after the title (#199)

.. _fixed-20:

Fixed
~~~~~

-  Already configured outputs not created (i.e. when creating reports)
-  KiCost+Internal variants: UTF-8 problems
-  KiCost+Internal variants: problem with ``variant`` field
   capitalization

.. _section-21:

`1.0.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.11.0...v1.0.0>`__ - 2022-05-10
------------------------------------------------------------------------------------

.. _added-20:

Added
~~~~~

-  General stuff:

   -  KiCad 6 support
   -  Import mechanism for filters, variants and globals (#88)
   -  Outputs can use the options of other outputs as base (extend
      them). (#112)
   -  A mechanism to avoid running some outputs by default. (#112)
   -  ``--cli-order`` option to generate outputs in arbitrary order.
      (#106)
   -  ``--quick-start`` option to create usable configs and outputs.

-  Filters and variants:

   -  Options to better control the rotation filter (#60 and #67):

      -  invert_bottom: bottom angles are inverted.
      -  skip_top: top components aren’t rotated.
      -  skip_bottom: bottom components aren’t rotated.

   -  Generic filter: options to match if a field is/isn’t defined.
   -  Another experimental mechanism to change 3D models according to
      the variant. (#103)
   -  Support for variants on KiCost output. (#106)

-  Expansion patterns:

   -  **%g** the ``file_id`` of the global variant.
   -  **%G** the ``name`` of the global variant.
   -  **%C1**, **%C2**, **%C3** and **%C4** the comments in the sch/pcb
      title block.
   -  **%bc**, **%bC1**, **%bC2**, **%bC3**, **%bC4**, **%bd**, **%bf**,
      **%bF**, **%bp** and **%br** board data
   -  **%sc**, **%sC1**, **%sC2**, **%sC3**, **%sC4**, **%sd**, **%sf**,
      **%sF**, **%sp** and **%sr** schematic data
   -  **%V** the variant name
   -  **%I** user defined ID for this output
   -  Now patterns are also expanded in the out_dir name.

-  Global options:

   -  Default global ``dir`` option.
   -  Default global ``units`` option.
   -  Global option to specify ``out_dir`` (like -d command line option)
   -  Global options to control the date format.
   -  Added global options to define the PCB details (``pcb_material``,
      ``solder_mask_color``, ``silk_screen_color`` and ``pcb_finish``)

-  New preflights:

   -  Commands to replace tags in the schematic and PCB (KiCad 5). (#93)
      Also a mechanism to define variables in KiCad 6. (#161)
   -  Annotate power components. (#76)
   -  Annotate according to PCB coordinates (#93)

-  New outputs:

   -  3D view render
   -  Report generation (for design house) (#93)
   -  QR codes generation and update: symbols and footprints. (#93)
   -  Print PCB layers in SVG/PDF/PS/EPS/PNG format.
   -  Join PDFs. (#156)
   -  Export PCB in GENCAD format. (#159)
   -  Datasheet downloader. (#119)

-  XLSX BoM: option to control the logo scale (#84)
-  PDF/SVG PCB Print:

   -  option ``hide_excluded`` to hide components marked by the
      ``exclude_filter``.
      https://forum.kicad.info/t/fab-drawing-for-only-through-hole-parts/
   -  mechanism to change the block title. (#102)
   -  KiCad 6 color theme selection.
   -  New ``pcb_print`` output with more flexibility and faster.

-  Internal BoM:

   -  option to avoid merging components with empty fields. Is named
      ``merge_both_blank`` and defaults to true.
   -  when a ``Value`` field can’t be interpreted as a ``number+unit``,
      and it contain at least one space, now we try to use the text
      before the space. This helps for cases like “10K 1%”.
   -  ``count_smd_tht`` option to compute SMD/THT stats. (#113)
   -  option to add text to the ``join`` list. (#108)
   -  two other options for the sorting criteria.
   -  XYRS support (you can generate position files using it)
   -  CSV ``hide_header`` option

-  Drill:

   -  Excellon: added ``route_mode_for_oval_holes`` option.
   -  Support for blind/buried vias. (#166)

-  SCH PDF Print: monochrome and no frame options.
-  Compress:

   -  Now you can compress files relative to the current working
      directory. So you can create a compressed file containing the
      source schematic and PCB files. (#93)
   -  Added an option to remove the files we compressed. (#192)

-  Support for new KiCost options ``split_extra_fields`` and
   ``board_qty``. (#120)
-  Position files now can include virtual components. (#106)
-  Support for ``--subst-models`` option for KiCad 6’s kicad2step.
   (#137)

.. _changed-16:

Changed
~~~~~~~

-  Internal BoM: now components with different Tolerance, Voltage,
   Current and/or Power fields aren’t grouped together. These fields are
   now part of the default ``group_fields``. (#79)
-  JLCPCB example, to match current recommendations
   (g200kg/kicad-gerberzipper#11)
-  Internal BoM: the field used for variants doesn’t produce conflicts.
   (#100)
-  The ``%v/%V`` expansion patterns now expand to the global variant
   when used in a context not related to variants. I.e. when a
   ``compress`` target expands ``%v``.
-  Now you get an error when defining two outputs with the same name.
-  The ``%d/%sd/%bd`` expansion patterns are now affected by the global
   ``date_format``. Can be disabled using ``date_reformat: false``.
   (#121)
-  The default output pattern now includes the ``output_id`` (%I)
-  The ``source`` path for ``compress`` now has pattern expansion (#152)

.. _fixed-21:

Fixed
~~~~~

-  Position files now defaults to use the auxiliary origin as KiCad. Can
   be disabled to use absolute coordinates. (#87)
-  Board View:

   -  flipped output. (#89)
   -  problems with netnames using spaces. (#90)
   -  get_targets not implemented. (#167)

-  Schematic

   -  load: problems with fields containing double quotes. (#98)
   -  Paper orientation was discarded on v5 files. (#150)

-  ``--list``: problems with layers and fields specific for the project.
   (INTI-CMNB/kibot_variants_arduprog#4)
-  Makefile: %VALUE not expanded in the directory targets.
-  KiCost variants:

   -  empty DNF fields shouldn’t be excluded. (#101)
   -  problems when setting a field in a variant that doesn’t exist when
      no variant is selected. (#105)

-  KiCost: list arguments wrongly passed. (#120)
-  PCB Print: to show the real name of the PCB file. (#102)
-  Compress: not expanding %VALUES in target dirs. (#111)
-  Gerber: job file didn’t use the global output pattern. (#116)
-  Warnings count
-  Update XML: Removed the side effect Bom. (#106)
-  Problems when using a hidden config file, using an output that needs
   the SCH, not specifying the SCH and more than one SCH was found.
   (#138)
-  3D: problems to download 3D models for native KiCad 6 files. (#171)
   (not imported from KiCad 5)
-  Problems when using page layout files with relative paths. (#174)

.. _section-22:

`0.11.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.10.1...v0.11.0>`__ - 2021-04-25
--------------------------------------------------------------------------------------

.. _added-21:

Added
~~~~~

-  ``erc_warnings`` preflight option to consider ERC warnings as errors.
-  Pattern expansion in the ``dir`` option for outputs (#58)
-  New filter types:

   -  ``suparts``: Adds support for KiCost’s subparts feature.
   -  ``field_rename``: Used to rename schematic fields.
   -  ``var_rename_kicost``: Like ``var_rename`` but using KiCost
      mechanism.

-  New KiCost variant style.
-  ``skip_if_no_field`` and ``invert`` options to the regex used in the
   generic filter.
-  Board view file format export (#69)
-  Experimental mechanism to change 3D models according to the variant.
-  Support for width, style and color in “wire notes” (#70)
-  Level and comment to columns in the XLSX BoM output.
-  Basic KiCost support (**experimental**).
-  Basic internal BoM and KiCost integration (**experimental**).

.. _changed-17:

Changed
~~~~~~~

-  Errors and warnings from KiAuto now are printed as errors and
   warnings.
-  Schematic dependencies are sorted in the generated Makefiles.
-  Makefile variables KIBOT, DEBUG and LOGFILE can be defined from
   outside.
-  Reference ranges of two elements no longer represented as ranges.
   Examples: “R1-R2” is now “R1 R2”, “R1-R3” remains unchanged.

.. _fixed-22:

Fixed
~~~~~

-  Problem when using E/DRC filters and the output dir didn’t exist.
-  Not all errors during makefile generation were caught (got a stack
   trace).
-  Output dirs created when generating a makefile for a compress target.
-  Problems with some SnapEDA libs (extra space in lib termination tag
   #57)
-  The “References” (plural) column is now coloured as “Reference”
   (singular)

.. _section-23:

`0.10.1 <https://github.com/INTI-CMNB/KiBot/compare/v0.10.0...v0.10.1>`__ - 2021-02-22
--------------------------------------------------------------------------------------

.. _added-22:

Added
~~~~~

-  GitLab CI workaround
-  Verbosity level is now passed to KiAuto

.. _section-24:

[0.10.0-4] - 2021-02-16
-----------------------

.. _fixed-23:

Fixed
~~~~~

-  Problem using Python 3.6 (ZipFile’s compresslevel arg needs 3.7)

.. _section-25:

[0.10.0-3] - 2021-02-16
-----------------------

.. _fixed-24:

Fixed
~~~~~

-  Problem using Python 3.6 (StreamHandler.setStream introduced in 3.7)

.. _section-26:

[0.10.0-2] - 2021-02-12
-----------------------

.. _fixed-25:

Fixed
~~~~~

-  Missing python3-distutils dependency on Debian package.

.. _section-27:

`0.10.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.9.0...v0.10.0>`__ - 2021-02-12
-------------------------------------------------------------------------------------

.. _added-23:

Added
~~~~~

-  The multipart id to references of multipart components others than
   part 1.
-  Internal BoM:

   -  ``no_conflict`` option to exclude fields from conflict detection.
   -  HTML tables can be sorted selecting a column (Java Script).
   -  You can consolidate more than one project in one BoM.

-  Support for KICAD_CONFIG_HOME defined from inside KiCad.
-  Now layers can be selected using the default KiCad names.
-  More control over the name of the drill and gerber files.
-  More options to customize the excellon output.
-  Custom reports for plot outputs (i.e. custom gerber job generation)
-  Example configurations for gerber and drill files for:

   -  `Elecrow <https://www.elecrow.com/>`__
   -  `FusionPCB <https://www.seeedstudio.io/fusion.html>`__
   -  `JLCPCB <https://jlcpcb.com/>`__
   -  `P-Ban <https://www.p-ban.com/>`__
   -  `PCBWay <https://www.pcbway.com>`__

-  Support for ZIP/TAR/RAR generation.
-  Makefile generation.
-  KiAuto time-out control.
-  Now you can import outputs from another config file.

.. _changed-18:

Changed
~~~~~~~

-  Now the default output name applies to the DRC and ERC report names.
   This provides more coherent file names.
-  Internal BoM: The “Quantity” column no longer includes the DNF/C
   status. This status was moved to a separated column named ``Status``.
   You can join both columns if you want.
-  Internal BoM: HTML rows are highlighted on hover (not just the cell).
-  Now information messages go to stdout (not stderr). Debug, warning
   and error messages still use stderr.
-  Now InteractiveHtmlBom can be installed just as a plugin.

.. _fixed-26:

Fixed
~~~~~

-  Extra data about drill marks in gerber files.
-  Problems using internal names for drill maps in gerb_drill output
   (#47).
-  Problems using layer suffixes containing non-ASCII chars
   (i.e. UTF-8).
-  Problems when using components with more than 10 subparts.

.. _section-28:

`0.9.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.8.1...v0.9.0>`__ - 2021-01-04
-----------------------------------------------------------------------------------

.. _added-24:

Added
~~~~~

-  iBoM output: file name patterns are allowed for the ``netlist_file``
   option.
-  File name patterns: %F is the name of the source file without
   extension, but with the path.
-  A hint for pip installations without using ``--no-compile``.
-  Support to field overwrite according to variant.
-  Support to generate negative X positions for the bottom layer.
-  A filter to rotate footprints in the position file (#28).
-  The step output now can download missing 3D models.

.. _changed-19:

Changed
~~~~~~~

-  Now position files are naturally sorted (R10 after R9, not after R1)
-  Position files in CSV format quotes only the columns that could
   contain an space. Just like KiCad does.

.. _fixed-27:

Fixed
~~~~~

-  Now we support missing field names in schematic library entries.
-  Generic filter ``include_only`` option worked only when debug
   enabled.

.. _section-29:

`0.8.1 <https://github.com/INTI-CMNB/KiBot/compare/v0.8.0...v0.8.1>`__ - 2020-12-09
-----------------------------------------------------------------------------------

.. _added-25:

Added
~~~~~

-  Internal BoM HTML: highlight cell when hover.
-  Internal BoM HTML: allow to jump to REF of row number using anchors.

.. _fixed-28:

Fixed
~~~~~

-  Internal BoM separator wasn’t applied when using ``use_alt``
-  Problems loading plug-ins when using ``pip``.

.. _section-30:

`0.8.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.7.0...v0.8.0>`__ - 2020-11-06
-----------------------------------------------------------------------------------

.. _added-26:

Added
~~~~~

-  The KiBoM and internal BoM generators now support configuring the
   separator used for the list of references.
-  Help for filters and variants.
-  Support for new ``pcbnew_do export`` options.
-  Filters for KiBot warnings.
-  Columns in position files can be selected, renamed and sorted as you
   like.

.. _fixed-29:

Fixed
~~~~~

-  KiBom variants when using multiple variants and a component uses more
   than one, specifying opposite rules.
-  Problems when using the ``pdf_pcb_print`` output and variants to
   remove a component with ridiculous pads that only has solder paste
   (no copper, nor even solder mask aperture).
-  Excellon drill output when using unified output and not using default
   KiCad names.

.. _section-31:

`0.7.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.6.2...v0.7.0>`__ - 2020-09-11
-----------------------------------------------------------------------------------

.. _added-27:

Added
~~~~~

-  Now variants are separated entities. Two flavors implemented: KiBoM
   and IBoM.
-  New filters entities. They work in complement with variants. All the
   filtering functionality found in KiBoM and IBoM is supported.
-  Most outputs now supports variants. You can:

   -  Mark not fitted components with a cross in the schematic
   -  Mark not fitted components with a cross in the \*.Fab layers of
      the PCB
   -  Remove solder paste from not fitted components
   -  Remove adhesive glue from not fitted components
   -  Exclude components from the BoM (also mark them as DNF and/or DNC
      (Do Not Change))
   -  Exclude components from the interactive BoM
   -  Remove not fitted components from the STEP file
   -  Exclude components from the position (pick & place) file

-  Default output file name format and default variant can be specified
   from the command line.

.. _fixed-30:

Fixed
~~~~~

-  Virtual components are always excluded from position files. Note you
   can change it using the variants mechanism.

.. _section-32:

`0.6.2 <https://github.com/INTI-CMNB/KiBot/compare/v0.6.1...v0.6.2>`__ - 2020-08-25
-----------------------------------------------------------------------------------

.. _changed-20:

Changed
~~~~~~~

-  Discarded spaces at the beginning and end of user fields when
   creating the internal BoM. They are usually mistakes that prevents
   grouping components.

.. _fixed-31:

Fixed
~~~~~

-  The variants logic for BoMs when a component requested to be only
   added to more than one variant.
-  Removed warnings about malformed values for DNF components indicating
   it in its value.
-  Problems with PcbDraw when generating PNG and JPG outputs. Now we use
   a more reliable conversion method when available.

.. _section-33:

`0.6.1 <https://github.com/INTI-CMNB/KiBot/compare/v0.6.0...v0.6.1>`__ - 2020-08-20
-----------------------------------------------------------------------------------

.. _added-28:

Added
~~~~~

-  More robust behavior on GUI dependent commands.

.. _changed-21:

Changed
~~~~~~~

-  Incorporated mcpy, no longer a dependency.

.. _fixed-32:

Fixed
~~~~~

-  Problems when using ``pip install`` without –no-compile. At least for
   user level install.

.. _section-34:

`0.6.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.5.0...v0.6.0>`__ - 2020-08-18
-----------------------------------------------------------------------------------

.. _added-29:

Added
~~~~~

-  Internal BoM generator, based on KiBoM code. This generator doesn’t
   need the netlist, works directly from the SCH. It features enhanced
   HTML and XLSX outputs, in addition to the CSV, TSV, TXT and XML
   traditional outputs.
-  Support for full KiBoM configuration from the YAML
-  Added output to print to an SVG file.
-  Added default output file name pattern. Can be applied to all
   outputs.
-  Unified output name:

   -  ``pdf_pcb_print.output`` can be used instead of
      ``pdf_pcb_print.output_name``
   -  ``gerber.gerber_job_file`` option to control the gerber job file
      name.
   -  ``output`` option to control the file name to all plot output
      formats.
   -  ``drill``, ``drill.map`` and ``position`` file names can be
      configured.
   -  Output file names supports expansion of various interesting values
      (base name, sheet title, revision, etc.).

-  The filters now accept the following aliases (suggested by @leoheck):

   -  ``filter_msg`` -> ``filter``
   -  ``error_number`` -> ``number``
   -  ``regexp`` -> ``regex``

.. _changed-22:

Changed
~~~~~~~

-  Default file names for:

   -  pdf_pcb_print: includes the used layers
   -  drill maps: uses drill instead of drl
   -  drill: uses drill instead of drl, used in gbr and drl.
   -  position: no -pos in CSVs
   -  step: adds -3D
   -  pdf_sch_print: adds -schematic
   -  IBoM: contains the project name.

.. _section-35:

`0.5.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.4.0...v0.5.0>`__ - 2020-07-11
-----------------------------------------------------------------------------------

.. _changed-23:

Changed
~~~~~~~

-  Removed the “plot” option “check_zone_fills”. Use the preflight
   option.
-  Drill outputs: map.type and report.filename now should be map and
   report. The old mechanism is currently supported, but deprecated.
-  Now the command line usage is more clearly documented, but also more
   strict.
-  The –list option doesn’t need a PCB file anymore. Note that passing
   it is now considered an error.
-  Now we test the PCB and/or SCH only when we are doing something that
   needs them.

.. _added-30:

Added
~~~~~

-  The layers entry is much more flexible now. Many changes, read the
   README.md
-  PcbDraw output.
-  -e/–schematic option to specify any schematic (not just derived from
   the PCB name.
-  -x/–example option to generate a complete configuration example.
-  –example supports –copy-options to copy the plot options from the PCB
   file.
-  Help for the supported outputs (–help-list-outputs, –help-outputs and
   –help-output)
-  Help for the supported preflights (–help-preflights)
-  Better YAML validation.
-  Added HPGL options:

   -  pen_number
   -  pen_speed

-  Added metric_units to DXF options
-  Added KiBoM options

   -  number
   -  variant
   -  conf
   -  separator

-  Added the following InteractiveHtmlBom options:

   -  dark_mode
   -  hide_pads
   -  show_fabrication
   -  hide_silkscreen
   -  highlight_pin1
   -  no_redraw_on_drag
   -  board_rotation
   -  checkboxes
   -  bom_view
   -  layer_view
   -  include_tracks
   -  include_nets
   -  sort_order
   -  no_blacklist_virtual
   -  blacklist_empty_val
   -  netlist_file
   -  extra_fields
   -  normalize_field_case
   -  variant_field
   -  variants_whitelist
   -  variants_blacklist
   -  dnp_field

.. _fixed-33:

Fixed
~~~~~

-  The ``sketch_plot`` option is now implemented.
-  ‘ignore_unconnected’ preflight wasn’t working.
-  The report of hwo many ERC/DRC errors we found.

.. _section-36:

`0.4.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.3.0...v0.4.0>`__ - 2020-06-17
-----------------------------------------------------------------------------------

.. _added-31:

Added
~~~~~

-  STEP 3D model generation
-  Support for unpatched InteractiveHtmlBom

.. _section-37:

`0.3.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.2.5...v0.3.0>`__ - 2020-06-14
-----------------------------------------------------------------------------------

.. _added-32:

Added
~~~~~

-  Better debug information when a BoM fails to be generated.
-  Support for compressed YAML files.

.. _changed-24:

Changed
~~~~~~~

-  Allow operations that doesn’t involve a PCB to run if the PCB file is
   missing or corrupted.
-  The ‘check_zone_fills’ option is now independent of ‘run_drc’

.. _fixed-34:

Fixed
~~~~~

-  Error codes that overlapped.

.. _section-38:

`0.2.5 <https://github.com/INTI-CMNB/KiBot/compare/v0.2.4...v0.2.5>`__ - 2020-06-11
-----------------------------------------------------------------------------------

.. _added-33:

Added
~~~~~

-  Tolerate config files without outputs
-  Mechanism to filter ERC/DRC errors

.. _fixed-35:

Fixed
~~~~~

-  All pcbnew plot formats generated gerber job files
-  Most formats that needed layers didn’t complain when omitted

.. _section-39:

`0.2.4 <https://github.com/INTI-CMNB/KiBot/compare/v0.2.3...v0.2.4>`__ - 2020-05-19
-----------------------------------------------------------------------------------

.. _changed-25:

Changed
~~~~~~~

-  Now kicad-automation-scripts 1.3.1 or newer is needed.

.. _fixed-36:

Fixed
~~~~~

-  Problems for kibom and print_sch outputs when the PCB name included a
   path.

.. _section-40:

`0.2.3 <https://github.com/INTI-CMNB/KiBot/compare/v0.2.2...v0.2.3>`__ - 2020-04-23
-----------------------------------------------------------------------------------

.. _added-34:

Added
~~~~~

-  List available targets

.. _section-41:

`0.2.2 <https://github.com/INTI-CMNB/KiBot/compare/v0.2.1...v0.2.2>`__ - 2020-04-20
-----------------------------------------------------------------------------------

.. _fixed-37:

Fixed
~~~~~

-  KiBoM temporal files, now removed
-  preflight tasks that didn’t honor –out-dir

.. _section-42:

`0.2.1 <https://github.com/INTI-CMNB/KiBot/compare/v0.2.0...v0.2.1>`__ - 2020-04-18
-----------------------------------------------------------------------------------

.. _fixed-38:

Fixed
~~~~~

-  Problem when the excellon drill target directory didn’t exist (now
   created)

.. _section-43:

`0.2.0 <https://github.com/INTI-CMNB/KiBot/compare/v0.1.1...v0.2.0>`__ - 2020-03-28
-----------------------------------------------------------------------------------

.. _added-35:

Added
~~~~~

-  Documentation for current functionality
-  Now the -b and -c options are optional, we guess the values
-  Inner layers sanitation, support for the names used in the PCB file
-  Better error report
-  Print the PCB and SCH in PDF format (we had plot)
-  KiBoM and InteractiveHtmlBoM support
-  Pre-flight: generation of the BoM in XML format
-  Pre-flight: DRC and ERC
-  Option to skip preflight actions
-  Option to select which outputs will be generated
-  Progress information
-  –version option

.. _fixed-39:

Fixed
~~~~~

-  Debian dependencies

.. _section-44:

`0.1.1 <https://github.com/INTI-CMNB/KiBot/releases/tag/v0.1.1>`__ - 2020-03-13
-------------------------------------------------------------------------------

.. _added-36:

Added
~~~~~

-  Pick & place position
-  Debian package
-  Gerber job generation
