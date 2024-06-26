.. Automatically generated by KiBot, please don't edit this file

.. index::
   pair: SVG (Scalable Vector Graphics); svg

SVG (Scalable Vector Graphics)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exports the PCB to a format suitable for 2D graphics software.
Unlike bitmaps SVG drawings can be scaled without losing resolution. |br|
This output is what you get from the File/Plot menu in pcbnew. |br|
The `pcb_print` is usually a better alternative. |br|
If you use custom fonts and/or colors please consult the `resources_dir` global variable. |br|

Type: ``svg``

Category: **PCB/docs**

Parameters:

-  **comment** :index:`: <pair: output - svg; comment>` [string=''] A comment for documentation purposes. It helps to identify the output.
-  **dir** :index:`: <pair: output - svg; dir>` [string='./'] Output directory for the generated files.
   If it starts with `+` the rest is concatenated to the default dir.
-  **layers** :index:`: <pair: output - svg; layers>` [list(dict)|list(string)|string] [all,selected,copper,technical,user,inners,outers]
   List of PCB layers to plot.

   -  Valid keys:

      -  ``description`` :index:`: <pair: output - svg - layers; description>` [string=''] A description for the layer, for documentation purposes.
         A default can be specified using the `layer_defaults` global option.
      -  ``layer`` :index:`: <pair: output - svg - layers; layer>` [string=''] Name of the layer. As you see it in KiCad.
      -  ``suffix`` :index:`: <pair: output - svg - layers; suffix>` [string=''] Suffix used in file names related to this layer. Derived from the name if not specified.
         A default can be specified using the `layer_defaults` global option.

-  **name** :index:`: <pair: output - svg; name>` [string=''] Used to identify this particular output definition.
   Avoid using `_` as first character. These names are reserved for KiBot.
-  **options** :index:`: <pair: output - svg; options>` [dict] Options for the `svg` output.

   -  Valid keys:

      -  **output** :index:`: <pair: output - svg - options; output>` [string='%f-%i%I%v.%x'] Output file name, the default KiCad name if empty.
         IMPORTANT! KiCad will always create the file using its own name and then we can rename it.
         For this reason you must avoid generating two variants at the same directory when one of
         them uses the default KiCad name. Affected by global options.
      -  **plot_sheet_reference** :index:`: <pair: output - svg - options; plot_sheet_reference>` [boolean=false] Include the frame and title block. Only available for KiCad 6+ and you get a poor result
         (i.e. always the default worksheet style, also problems expanding text variables).
         The `pcb_print` output can do a better job for PDF, SVG, PS, EPS and PNG outputs.
      -  **scaling** :index:`: <pair: output - svg - options; scaling>` [number=1] Scale factor (0 means autoscaling).
      -  ``custom_reports`` :index:`: <pair: output - svg - options; custom_reports>` [list(dict)] A list of customized reports for the manufacturer.

         -  Valid keys:

            -  ``content`` :index:`: <pair: output - svg - options - custom_reports; content>` [string=''] Content for the report. Use ``${basename}`` for the project name without extension.
               Use ``${filename(LAYER)}`` for the file corresponding to LAYER.
            -  ``output`` :index:`: <pair: output - svg - options - custom_reports; output>` [string='Custom_report.txt'] File name for the custom report.

      -  ``dnf_filter`` :index:`: <pair: output - svg - options; dnf_filter>` [string|list(string)='_none'] Name of the filter to mark components as not fitted.
         A short-cut to use for simple cases where a variant is an overkill.

      -  ``drill_marks`` :index:`: <pair: output - svg - options; drill_marks>` [string='full'] [none,small,full] What to use to indicate the drill places, can be none, small or full (for real scale).
      -  ``edge_cut_extension`` :index:`: <pair: output - svg - options; edge_cut_extension>` [string=''] Used to configure the edge cuts layer extension for Protel mode. Include the dot.
      -  ``exclude_edge_layer`` :index:`: <pair: output - svg - options; exclude_edge_layer>` [boolean=true] Do not include the PCB edge layer.
      -  ``exclude_pads_from_silkscreen`` :index:`: <pair: output - svg - options; exclude_pads_from_silkscreen>` [boolean=false] Do not plot the component pads in the silk screen (KiCad 5.x only).
      -  ``force_plot_invisible_refs_vals`` :index:`: <pair: output - svg - options; force_plot_invisible_refs_vals>` [boolean=false] Include references and values even when they are marked as invisible.
      -  ``individual_page_scaling`` :index:`: <pair: output - svg - options; individual_page_scaling>` [boolean=true] Tell KiCad to apply the scaling for each layer as a separated entity.
         Disabling it the pages are coherent and can be superposed.
      -  ``inner_extension_pattern`` :index:`: <pair: output - svg - options; inner_extension_pattern>` [string=''] Used to change the Protel style extensions for inner layers.
         The replacement pattern can contain %n for the inner layer number and %N for the layer number.
         Example '.g%n'.
      -  ``limit_viewbox`` :index:`: <pair: output - svg - options; limit_viewbox>` [boolean=false] When enabled the view box is limited to a selected area.
         This option can't be enabled when using a scale.
      -  ``line_width`` :index:`: <pair: output - svg - options; line_width>` [number=0.25] [0.02,2] For objects without width [mm] (KiCad 5).
      -  ``margin`` :index:`: <pair: output - svg - options; margin>` [number|dict] Margin around the view box [mm].
         Using a number the margin is the same in the four directions.
         See `limit_viewbox` option.

         -  Valid keys:

            -  ``bottom`` :index:`: <pair: output - svg - options - margin; bottom>` [number=0] Bottom margin [mm].
            -  ``left`` :index:`: <pair: output - svg - options - margin; left>` [number=0] Left margin [mm].
            -  ``right`` :index:`: <pair: output - svg - options - margin; right>` [number=0] Right margin [mm].
            -  ``top`` :index:`: <pair: output - svg - options - margin; top>` [number=0] Top margin [mm].

      -  ``mirror_plot`` :index:`: <pair: output - svg - options; mirror_plot>` [boolean=false] Plot mirrored.
      -  ``negative_plot`` :index:`: <pair: output - svg - options; negative_plot>` [boolean=false] Invert black and white.
      -  ``plot_footprint_refs`` :index:`: <pair: output - svg - options; plot_footprint_refs>` [boolean=true] Include the footprint references.
      -  ``plot_footprint_values`` :index:`: <pair: output - svg - options; plot_footprint_values>` [boolean=true] Include the footprint values.
      -  ``pre_transform`` :index:`: <pair: output - svg - options; pre_transform>` [string|list(string)='_none'] Name of the filter to transform fields before applying other filters.
         A short-cut to use for simple cases where a variant is an overkill.

      -  ``size_detection`` :index:`: <pair: output - svg - options; size_detection>` [string='kicad_edge'] [kicad_edge,kicad_all] Method used to detect the size of the view box.
         The `kicad_edge` method uses the size of the board as reported by KiCad,
         components that extend beyond the PCB limit will be cropped. You can manually
         adjust the margin to make them visible.
         The `kicad_all` method uses the whole size reported by KiCad. Usually includes extra space.
         See `limit_viewbox` option.
      -  ``sketch_pad_line_width`` :index:`: <pair: output - svg - options; sketch_pad_line_width>` [number=0.1] Line width for the sketched pads [mm], see `sketch_pads_on_fab_layers` (KiCad 6+)
         Note that this value is currently ignored by KiCad (6.0.9).
      -  ``sketch_pads_on_fab_layers`` :index:`: <pair: output - svg - options; sketch_pads_on_fab_layers>` [boolean=false] Draw only the outline of the pads on the \\*.Fab layers (KiCad 6+).
      -  ``svg_precision`` :index:`: <pair: output - svg - options; svg_precision>` [number=4] [0,6] Scale factor used to represent 1 mm in the SVG (KiCad 6).
         The value is how much zeros has the multiplier (1 mm = 10 power `svg_precision` units).
         Note that for an A4 paper Firefox 91 and Chrome 105 can't handle more than 5.
      -  ``tent_vias`` :index:`: <pair: output - svg - options; tent_vias>` [boolean=true] Cover the vias.
      -  ``uppercase_extensions`` :index:`: <pair: output - svg - options; uppercase_extensions>` [boolean=false] Use uppercase names for the extensions.
      -  ``variant`` :index:`: <pair: output - svg - options; variant>` [string=''] Board variant to apply.

-  **type** :index:`: <pair: output - svg; type>` 'svg'
-  ``category`` :index:`: <pair: output - svg; category>` [string|list(string)=''] The category for this output. If not specified an internally defined category is used.
   Categories looks like file system paths, i.e. **PCB/fabrication/gerber**.
   The categories are currently used for `navigate_results`.

-  ``disable_run_by_default`` :index:`: <pair: output - svg; disable_run_by_default>` [string|boolean] Use it to disable the `run_by_default` status of other output.
   Useful when this output extends another and you don't want to generate the original.
   Use the boolean true value to disable the output you are extending.
-  ``extends`` :index:`: <pair: output - svg; extends>` [string=''] Copy the `options` section from the indicated output.
   Used to inherit options from another output of the same type.
-  ``groups`` :index:`: <pair: output - svg; groups>` [string|list(string)=''] One or more groups to add this output. In order to catch typos
   we recommend to add outputs only to existing groups. You can create an empty group if
   needed.

-  ``output_id`` :index:`: <pair: output - svg; output_id>` [string=''] Text to use for the %I expansion content. To differentiate variations of this output.
-  ``priority`` :index:`: <pair: output - svg; priority>` [number=50] [0,100] Priority for this output. High priority outputs are created first.
   Internally we use 10 for low priority, 90 for high priority and 50 for most outputs.
-  ``run_by_default`` :index:`: <pair: output - svg; run_by_default>` [boolean=true] When enabled this output will be created when no specific outputs are requested.

