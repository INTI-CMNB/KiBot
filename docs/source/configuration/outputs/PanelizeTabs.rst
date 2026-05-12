.. _PanelizeTabs:

:orphan:


PanelizeTabs parameters
~~~~~~~~~~~~~~~~~~~~~~~

-  **type** :index:`: <pair: output - panelize - options - configs - tabs; type>` ''
-  ``arg`` :index:`: <pair: output - panelize - options - configs - tabs; arg>` [:ref:`string <string>`] (default: ``''``) Argument to pass to the plugin. Used for *plugin*.
-  ``code`` :index:`: <pair: output - panelize - options - configs - tabs; code>` [:ref:`string <string>`] (default: ``''``) Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin*.
-  ``cutout`` :index:`: <pair: output - panelize - options - configs - tabs; cutout>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``1``) When your design features open pockets on the side, this parameter specifies extra cutout
   depth in order to ensure that a sharp corner of the pocket can be milled. Used for *full*.
-  ``hcount`` :index:`: <pair: output - panelize - options - configs - tabs; hcount>` [:ref:`number <number>`] (default: ``1``) Number of tabs in the horizontal direction. Used for *fixed*.
-  ``hwidth`` :index:`: <pair: output - panelize - options - configs - tabs; hwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) The width of tabs in the horizontal direction. Used for *fixed* and *spacing*.
-  *min_distance* :index:`: <pair: output - panelize - options - configs - tabs; min_distance>` Alias for mindistance.
-  ``mindistance`` :index:`: <pair: output - panelize - options - configs - tabs; mindistance>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``0``) Minimal spacing between the tabs. If there are too many tabs, their count is reduced.
   Used for *fixed*.
-  *patch_corners* :index:`: <pair: output - panelize - options - configs - tabs; patch_corners>` Alias for patchcorners.
-  ``patchcorners`` :index:`: <pair: output - panelize - options - configs - tabs; patchcorners>` [:ref:`boolean <boolean>`] (default: ``true``) The full tabs are appended to the nearest flat face of the PCB. If the PCB has sharp corners, you want to
   add patches of substrate to these corners. However, if the PCB has fillet or miter, you don't want to
   apply the patches.
-  ``spacing`` :index:`: <pair: output - panelize - options - configs - tabs; spacing>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``10``) The maximum spacing of the tabs. Used for *spacing*.
-  *tab_footprints* :index:`: <pair: output - panelize - options - configs - tabs; tab_footprints>` Alias for tabfootprints.
-  ``tabfootprints`` :index:`: <pair: output - panelize - options - configs - tabs; tabfootprints>` [:ref:`string <string>`] (default: ``'kikit:Tab'``) The footprint/s used for the *annotation* type. You can specify a list of footprints separated by comma.
-  ``vcount`` :index:`: <pair: output - panelize - options - configs - tabs; vcount>` [:ref:`number <number>`] (default: ``1``) Number of tabs in the vertical direction. Used for *fixed*.
-  ``vwidth`` :index:`: <pair: output - panelize - options - configs - tabs; vwidth>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) The width of tabs in the vertical direction. Used for *fixed* and *spacing*.
-  ``width`` :index:`: <pair: output - panelize - options - configs - tabs; width>` [:ref:`number <number>` | :ref:`string <string>`] (default: ``3``) The width of tabs in both directions. Overrides both `vwidth` and `hwidth`.
   Used for *fixed*, *spacing*, *corner* and *annotation*.

