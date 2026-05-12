.. _Stencil_For_Jig_Options:

:orphan:


Stencil_For_Jig_Options parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  *jig_height* :index:`: <pair: output - stencil_for_jig - options; jig_height>` Alias for jigheight.
-  *jig_thickness* :index:`: <pair: output - stencil_for_jig - options; jig_thickness>` Alias for jigthickness.
-  *jig_width* :index:`: <pair: output - stencil_for_jig - options; jig_width>` Alias for jigwidth.
-  **jigheight** :index:`: <pair: output - stencil_for_jig - options; jigheight>` [:ref:`number <number>`] (default: ``100``) Jig frame height [mm].
-  **jigthickness** :index:`: <pair: output - stencil_for_jig - options; jigthickness>` [:ref:`number <number>`] (default: ``3``) Jig thickness [mm].
-  **jigwidth** :index:`: <pair: output - stencil_for_jig - options; jigwidth>` [:ref:`number <number>`] (default: ``100``) Jig frame width [mm].
-  **output** :index:`: <pair: output - stencil_for_jig - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i='stencil_for_jig_top'|'stencil_for_jig_bottom',
   %x='stl'|'scad'|'gbp'|'gtp'|'gbrjob'|'png'). Affected by global options.
-  ``create_preview`` :index:`: <pair: output - stencil_for_jig - options; create_preview>` [:ref:`boolean <boolean>`] (default: ``true``) Creates a PNG showing the generated 3D model.
-  ``cutout`` :index:`: <pair: output - stencil_for_jig - options; cutout>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] [:ref:`comma separated <comma_sep>`] List of components to add a cutout based on the component courtyard.
   This is useful when you have already pre-populated board and you want to populate more
   components.
-  ``dnf_filter`` :index:`: <pair: output - stencil_for_jig - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - stencil_for_jig - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``include_scad`` :index:`: <pair: output - stencil_for_jig - options; include_scad>` [:ref:`boolean <boolean>`] (default: ``true``) Include the generated OpenSCAD files.
-  *pcb_thickness* :index:`: <pair: output - stencil_for_jig - options; pcb_thickness>` Alias for pcbthickness.
-  ``pcbthickness`` :index:`: <pair: output - stencil_for_jig - options; pcbthickness>` [:ref:`number <number>`] (default: ``0``) PCB thickness [mm]. If 0 we will ask KiCad.
-  ``pre_transform`` :index:`: <pair: output - stencil_for_jig - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  *register_border_inner* :index:`: <pair: output - stencil_for_jig - options; register_border_inner>` Alias for registerborderinner.
-  *register_border_outer* :index:`: <pair: output - stencil_for_jig - options; register_border_outer>` Alias for registerborderouter.
-  ``registerborderinner`` :index:`: <pair: output - stencil_for_jig - options; registerborderinner>` [:ref:`number <number>`] (default: ``1``) Inner register border [mm].
-  ``registerborderouter`` :index:`: <pair: output - stencil_for_jig - options; registerborderouter>` [:ref:`number <number>`] (default: ``3``) Outer register border [mm].
-  ``side`` :index:`: <pair: output - stencil_for_jig - options; side>` [:ref:`string <string>`] (default: ``'auto'``) (choices: "top", "bottom", "auto", "both") Which side of the PCB we want. Using `auto` will detect which
   side contains solder paste.
-  ``tolerance`` :index:`: <pair: output - stencil_for_jig - options; tolerance>` [:ref:`number <number>`] (default: ``0.05``) Enlarges the register by the tolerance value [mm].
-  ``variant`` :index:`: <pair: output - stencil_for_jig - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

