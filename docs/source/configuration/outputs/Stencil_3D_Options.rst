.. _Stencil_3D_Options:

:orphan:


Stencil_3D_Options parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _Stencil_3D_Options_output:

-  **output** :index:`: <pair: output - stencil_3d - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i='stencil_3d_top'|'stencil_3d_bottom'|'stencil_3d_edge',
   %x='stl'|'scad'|'dxf'|'png'). Affected by global options.

.. _Stencil_3D_Options_thickness:

-  **thickness** :index:`: <pair: output - stencil_3d - options; thickness>` [:ref:`number <number>`] (default: ``0.15``) Stencil thickness [mm]. Defines amount of paste dispensed.

.. _Stencil_3D_Options_create_preview:

-  ``create_preview`` :index:`: <pair: output - stencil_3d - options; create_preview>` [:ref:`boolean <boolean>`] (default: ``true``) Creates a PNG showing the generated 3D model.

.. _Stencil_3D_Options_cutout:

-  ``cutout`` :index:`: <pair: output - stencil_3d - options; cutout>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] [:ref:`comma separated <comma_sep>`] List of components to add a cutout based on the component courtyard.
   This is useful when you have already pre-populated board and you want to populate more
   components.

.. _Stencil_3D_Options_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - stencil_3d - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Stencil_3D_Options_enlarge_holes:

-  *enlarge_holes* :index:`: <pair: output - stencil_3d - options; enlarge_holes>` Alias for enlarge_holes.

.. _Stencil_3D_Options_enlargeholes:

-  ``enlargeholes`` :index:`: <pair: output - stencil_3d - options; enlargeholes>` [:ref:`number <number>`] (default: ``0``) Enlarge pad holes by x mm.

.. _Stencil_3D_Options_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - stencil_3d - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Stencil_3D_Options_frame_clearance:

-  *frame_clearance* :index:`: <pair: output - stencil_3d - options; frame_clearance>` Alias for frameclearance.

.. _Stencil_3D_Options_frame_width:

-  *frame_width* :index:`: <pair: output - stencil_3d - options; frame_width>` Alias for framewidth.

.. _Stencil_3D_Options_frameclearance:

-  ``frameclearance`` :index:`: <pair: output - stencil_3d - options; frameclearance>` [:ref:`number <number>`] (default: ``0``) Clearance for the stencil register [mm].

.. _Stencil_3D_Options_framewidth:

-  ``framewidth`` :index:`: <pair: output - stencil_3d - options; framewidth>` [:ref:`number <number>`] (default: ``1``) Register frame width.

.. _Stencil_3D_Options_include_scad:

-  ``include_scad`` :index:`: <pair: output - stencil_3d - options; include_scad>` [:ref:`boolean <boolean>`] (default: ``true``) Include the generated OpenSCAD files.
   Note that this also includes the DXF files.

.. _Stencil_3D_Options_pcb_thickness:

-  *pcb_thickness* :index:`: <pair: output - stencil_3d - options; pcb_thickness>` Alias for pcbthickness.

.. _Stencil_3D_Options_pcbthickness:

-  ``pcbthickness`` :index:`: <pair: output - stencil_3d - options; pcbthickness>` [:ref:`number <number>`] (default: ``0``) PCB thickness [mm]. If 0 we will ask KiCad.

.. _Stencil_3D_Options_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - stencil_3d - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _Stencil_3D_Options_side:

-  ``side`` :index:`: <pair: output - stencil_3d - options; side>` [:ref:`string <string>`] (default: ``'auto'``) (choices: "top", "bottom", "auto", "both") Which side of the PCB we want. Using `auto` will detect which
   side contains solder paste.

.. _Stencil_3D_Options_variant:

-  ``variant`` :index:`: <pair: output - stencil_3d - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

