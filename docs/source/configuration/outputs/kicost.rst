.. Automatically generated by KiBot, please don't edit this file

.. index::
   pair: KiCost (KiCad Cost calculator); kicost

KiCost (KiCad Cost calculator)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generates a spreadsheet containing components costs.
For more information: https://github.com/INTI-CMNB/KiCost
This output is what you get from the KiCost plug-in (eeschema). |br|
You can get KiCost costs using the internal BoM output (`bom`). |br|

Type: ``kicost``


Parameters:

-  **comment** :index:`: <pair: output - kicost; comment>` [string=''] A comment for documentation purposes. It helps to identify the output.
-  **dir** :index:`: <pair: output - kicost; dir>` [string='./'] Output directory for the generated files.
   If it starts with `+` the rest is concatenated to the default dir.
-  **name** :index:`: <pair: output - kicost; name>` [string=''] Used to identify this particular output definition.
   Avoid using `_` as first character. These names are reserved for KiBot.
-  **options** :index:`: <pair: output - kicost; options>` [dict] Options for the `kicost` output.

   -  Valid keys:

      -  *board_qty* :index:`: <pair: output - kicost - options; board_qty>` Alias for number.
      -  **currency** :index:`: <pair: output - kicost - options; currency>` [string|list(string)=USD] Currency priority. Use ISO4217 codes (i.e. USD, EUR).

      -  **distributors** :index:`: <pair: output - kicost - options; distributors>` [string|list(string)] Include this distributors list. Default is all the available.

      -  **no_distributors** :index:`: <pair: output - kicost - options; no_distributors>` [string|list(string)] Exclude this distributors list. They are removed after computing `distributors`.

      -  **no_price** :index:`: <pair: output - kicost - options; no_price>` [boolean=false] Do not look for components price. For testing purposes.
      -  **number** :index:`: <pair: output - kicost - options; number>` [number=100] Number of boards to build (components multiplier).
      -  **output** :index:`: <pair: output - kicost - options; output>` [string='%f-%i%I%v.%x'] Filename for the output (%i=kicost, %x=xlsx). Affected by global options.
      -  ``aggregate`` :index:`: <pair: output - kicost - options; aggregate>` [list(dict)] Add components from other projects.

         -  Valid keys:

            -  *board_qty* :index:`: <pair: output - kicost - options - aggregate; board_qty>` Alias for number.
            -  **file** :index:`: <pair: output - kicost - options - aggregate; file>` [string=''] Name of the XML to aggregate.
            -  **number** :index:`: <pair: output - kicost - options - aggregate; number>` [number=100] Number of boards to build (components multiplier).
            -  ``variant`` :index:`: <pair: output - kicost - options - aggregate; variant>` [string=' '] Variant for this project.

      -  ``dnf_filter`` :index:`: <pair: output - kicost - options; dnf_filter>` [string|list(string)='_none'] Name of the filter to mark components as not fitted.
         A short-cut to use for simple cases where a variant is an overkill.
         Don't use the `kicost_variant` when using internal variants/filters.

      -  ``fields`` :index:`: <pair: output - kicost - options; fields>` [string|list(string)] List of fields to be added to the global data section.

      -  ``group_fields`` :index:`: <pair: output - kicost - options; group_fields>` [string|list(string)] List of fields that can be different for a group.
         Parts with differences in these fields are grouped together, but displayed individually.

      -  ``ignore_fields`` :index:`: <pair: output - kicost - options; ignore_fields>` [string|list(string)] List of fields to be ignored.

      -  ``kicost_variant`` :index:`: <pair: output - kicost - options; kicost_variant>` [string=''] Regular expression to match the variant field (KiCost option, not internal variants).
      -  ``no_collapse`` :index:`: <pair: output - kicost - options; no_collapse>` [boolean=false] Do not collapse the part references (collapse=R1-R4).
      -  ``pre_transform`` :index:`: <pair: output - kicost - options; pre_transform>` [string|list(string)='_none'] Name of the filter to transform fields before applying other filters.
         A short-cut to use for simple cases where a variant is an overkill.

      -  ``show_cat_url`` :index:`: <pair: output - kicost - options; show_cat_url>` [boolean=false] Include the catalogue links in the catalogue code.
      -  ``split_extra_fields`` :index:`: <pair: output - kicost - options; split_extra_fields>` [string|list(string)] Declare part fields to include in multipart split process.

      -  ``translate_fields`` :index:`: <pair: output - kicost - options; translate_fields>` [list(dict)] Fields to rename (KiCost option, not internal filters).

         -  Valid keys:

            -  ``field`` :index:`: <pair: output - kicost - options - translate_fields; field>` [string=''] Name of the field to rename.
            -  ``name`` :index:`: <pair: output - kicost - options - translate_fields; name>` [string=''] New name.

      -  ``variant`` :index:`: <pair: output - kicost - options; variant>` [string=''] Board variant to apply.
         Don't use the `kicost_variant` when using internal variants/filters.

-  **type** :index:`: <pair: output - kicost; type>` 'kicost'
-  ``category`` :index:`: <pair: output - kicost; category>` [string|list(string)=''] The category for this output. If not specified an internally defined category is used.
   Categories looks like file system paths, i.e. **PCB/fabrication/gerber**.
   The categories are currently used for `navigate_results`.

-  ``disable_run_by_default`` :index:`: <pair: output - kicost; disable_run_by_default>` [string|boolean] Use it to disable the `run_by_default` status of other output.
   Useful when this output extends another and you don't want to generate the original.
   Use the boolean true value to disable the output you are extending.
-  ``extends`` :index:`: <pair: output - kicost; extends>` [string=''] Copy the `options` section from the indicated output.
   Used to inherit options from another output of the same type.
-  ``groups`` :index:`: <pair: output - kicost; groups>` [string|list(string)=''] One or more groups to add this output. In order to catch typos
   we recommend to add outputs only to existing groups. You can create an empty group if
   needed.

-  ``output_id`` :index:`: <pair: output - kicost; output_id>` [string=''] Text to use for the %I expansion content. To differentiate variations of this output.
-  ``priority`` :index:`: <pair: output - kicost; priority>` [number=50] [0,100] Priority for this output. High priority outputs are created first.
   Internally we use 10 for low priority, 90 for high priority and 50 for most outputs.
-  ``run_by_default`` :index:`: <pair: output - kicost; run_by_default>` [boolean=true] When enabled this output will be created when no specific outputs are requested.

