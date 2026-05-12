.. _ReportOptions:

:orphan:


ReportOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~

-  **convert_to** :index:`: <pair: output - report - options; convert_to>` [:ref:`string <string>`] (default: ``'pdf'``) Target format for the report conversion. See `do_convert`.
-  **do_convert** :index:`: <pair: output - report - options; do_convert>` [:ref:`boolean <boolean>`] (default: ``false``) Run `Pandoc` to convert the report. Note that Pandoc must be installed.
   The conversion is done assuming the report is in `convert_from` format. |br|
   The output file will be in `convert_to` format. |br|
   The available formats depends on the `Pandoc` installation. |br|
   In CI/CD environments: the `kicad_auto_test` docker image contains it. |br|
   In Debian/Ubuntu environments: install `pandoc`, `texlive`, `texlive-latex-base` and `texlive-latex-recommended`.
-  **output** :index:`: <pair: output - report - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Output file name (%i='report', %x='txt'). Affected by global options.
-  **template** :index:`: <pair: output - report - options; template>` [:ref:`string <string>`] (default: ``'full'``) (choices: "full", "full_svg", "simple", "testpoints", "total_components", "total_components_dnp") (also accepts any string) Name for one of the internal
   templates or a custom template file. |br|
   Environment variables and ~ are allowed. |br|
   The `total_components` template can be used to include a table containing components count
   in your PCB. Take a look at the `docs/samples/Component_Count_Table/` in the repo. |br|
   Note: when converting to PDF PanDoc can fail on some Unicode values (use `simple_ASCII`). |br|
   Note: the testpoint variables uses the `testpoint` fabrication attribute of pads.
-  ``alloy_specific_gravity`` :index:`: <pair: output - report - options; alloy_specific_gravity>` [:ref:`number <number>`] (default: ``7.4``) Specific gravity of the alloy used for the solder paste, in g/cm3. Used to compute solder paste usage.
-  ``convert_from`` :index:`: <pair: output - report - options; convert_from>` [:ref:`string <string>`] (default: ``'markdown'``) Original format for the report conversion. Current templates are `markdown`. See `do_convert`.
-  ``converted_output`` :index:`: <pair: output - report - options; converted_output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Converted output file name (%i='report', %x=`convert_to`).
   Note that the extension should match the `convert_to` value. Affected by global options.
-  ``csv_remove_leading_spaces`` :index:`: <pair: output - report - options; csv_remove_leading_spaces>` [:ref:`boolean <boolean>`] (default: ``false``) Remove any leading spaces/tabs at the end of each separator.
   Used por templates that generates CSV files where elements are aligned for easier reading.
-  ``display_trailing_zeros`` :index:`: <pair: output - report - options; display_trailing_zeros>` [:ref:`boolean <boolean>`] (default: ``false``) Display trailing zeros.
-  ``dnf_filter`` :index:`: <pair: output - report - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``eurocircuits_class_target`` :index:`: <pair: output - report - options; eurocircuits_class_target>` [:ref:`string <string>`] (default: ``'10F'``) Which Eurocircuits class are we aiming at.
-  ``eurocircuits_reduce_holes`` :index:`: <pair: output - report - options; eurocircuits_reduce_holes>` [:ref:`number <number>`] (default: ``0.45``) When computing the Eurocircuits category: Final holes sizes smaller or equal to this given
   diameter can be reduced to accommodate the correct annular ring values. |br|
   Use 0 to disable it.
-  ``exclude_filter`` :index:`: <pair: output - report - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``flux_specific_gravity`` :index:`: <pair: output - report - options; flux_specific_gravity>` [:ref:`number <number>`] (default: ``1.0``) Specific gravity of the flux used for the solder paste, in g/cm3. Used to compute solder paste usage.
-  ``in_digits`` :index:`: <pair: output - report - options; in_digits>` [:ref:`number <number>`] (default: ``2``) Number of digits for values expressed in inches.
-  ``mils_digits`` :index:`: <pair: output - report - options; mils_digits>` [:ref:`number <number>`] (default: ``0``) Number of digits for values expressed in mils.
-  ``mm_digits`` :index:`: <pair: output - report - options; mm_digits>` [:ref:`number <number>`] (default: ``2``) Number of digits for values expressed in mm.
-  ``pre_transform`` :index:`: <pair: output - report - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``solder_paste_metal_amount`` :index:`: <pair: output - report - options; solder_paste_metal_amount>` [:ref:`number <number>`] (default: ``87.75``) (range: 0 to 100) Amount of metal in the solder paste (percentage). Used to compute solder paste usage.
-  ``stencil_thickness`` :index:`: <pair: output - report - options; stencil_thickness>` [:ref:`number <number>`] (default: ``0.12``) Stencil thickness in mm. Used to compute solder paste usage.
-  ``variant`` :index:`: <pair: output - report - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

