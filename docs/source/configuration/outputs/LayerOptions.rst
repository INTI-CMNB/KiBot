.. _LayerOptions:

:orphan:


LayerOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~


.. _LayerOptions_color:

-  ``color`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; color>` [:ref:`string <string>`] (default: ``''``) Color used for this layer.
   KiCad 6+: don't forget the alpha channel for layers like the solder mask.

.. _LayerOptions_description:

-  ``description`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; description>` [:ref:`string <string>`] (default: ``''``) A description for the layer, for documentation purposes.
   A default can be specified using the `layer_defaults` global option.

.. _LayerOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components before printing this layer.
   This option affects only this layer. |br|
   You should also set `plot_footprint_values` and `sketch_pads_on_fab` to false.


.. _LayerOptions_force_plot_invisible_refs_vals:

-  ``force_plot_invisible_refs_vals`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; force_plot_invisible_refs_vals>` [:ref:`boolean <boolean>`] (default: ``false``) Include references and values even when they are marked as invisible.
   Not available on KiCad 9.0.1 and newer.

.. _LayerOptions_layer:

-  ``layer`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; layer>` [:ref:`string <string>`] (default: ``''``) Name of the layer. As you see it in KiCad.

.. _LayerOptions_plot_footprint_refs:

-  ``plot_footprint_refs`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; plot_footprint_refs>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint references.

.. _LayerOptions_plot_footprint_values:

-  ``plot_footprint_values`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; plot_footprint_values>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint values.

.. _LayerOptions_sketch_pads_on_fab_layers:

-  ``sketch_pads_on_fab_layers`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; sketch_pads_on_fab_layers>` [:ref:`boolean <boolean>`] (default: ``false``) Draw the outline of the pads on the \\*.Fab layers (KiCad 6+).
   When not defined we use the default value for the page.

.. _LayerOptions_suffix:

-  ``suffix`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; suffix>` [:ref:`string <string>`] (default: ``''``) Suffix used in file names related to this layer. Derived from the name if not specified.
   A default can be specified using the `layer_defaults` global option.

.. _LayerOptions_use_for_center:

-  ``use_for_center`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; use_for_center>` [:ref:`boolean <boolean>`] (default: ``true``) Use this layer for centering purposes.
   You can invert the meaning using the `invert_use_for_center` option.

