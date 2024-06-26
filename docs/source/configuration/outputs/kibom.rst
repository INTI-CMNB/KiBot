.. Automatically generated by KiBot, please don't edit this file

.. index::
   pair: KiBoM (KiCad Bill of Materials); kibom

KiBoM (KiCad Bill of Materials)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Used to generate the BoM in HTML or CSV format using the KiBoM plug-in.
For more information: https://github.com/INTI-CMNB/KiBoM
Note that this output is provided as a compatibility tool. |br|
We recommend using the `bom` output instead. |br|
This output is what you get from the 'Tools/Generate Bill of Materials' menu in eeschema. |br|
Also note that here the KiBot concept of variants doesn't apply. |br|

Type: ``kibom``


Parameters:

-  **comment** :index:`: <pair: output - kibom; comment>` [string=''] A comment for documentation purposes. It helps to identify the output.
-  **dir** :index:`: <pair: output - kibom; dir>` [string='./'] Output directory for the generated files.
   If it starts with `+` the rest is concatenated to the default dir.
-  **name** :index:`: <pair: output - kibom; name>` [string=''] Used to identify this particular output definition.
   Avoid using `_` as first character. These names are reserved for KiBot.
-  **options** :index:`: <pair: output - kibom; options>` [dict] Options for the `kibom` output.

   -  Valid keys:

      -  **format** :index:`: <pair: output - kibom - options; format>` [string='HTML'] [HTML,CSV,XML,XLSX] Format for the BoM.
      -  **number** :index:`: <pair: output - kibom - options; number>` [number=1] Number of boards to build (components multiplier).
      -  **output** :index:`: <pair: output - kibom - options; output>` [string='%f-%i%I%v.%x'] Filename for the output (%i=bom). Affected by global options.
      -  ``conf`` :index:`: <pair: output - kibom - options; conf>` [string|dict] BoM configuration file, relative to PCB. Environment variables and ~ allowed.
         You can also define the configuration here, will be stored in `config.kibom.ini`.

         -  Valid keys:

            -  **columns** :index:`: <pair: output - kibom - options - conf; columns>` [list(dict)|list(string)] List of columns to display.
               Can be just the name of the field.

               -  Valid keys:

                  -  **field** :index:`: <pair: output - kibom - options - conf - columns; field>` [string=''] Name of the field to use for this column.
                     Use `_field_lcsc_part` to get the value defined in the global options.
                  -  **name** :index:`: <pair: output - kibom - options - conf - columns; name>` [string=''] Name to display in the header. The field is used when empty.
                  -  ``join`` :index:`: <pair: output - kibom - options - conf - columns; join>` [list(string)|string=''] List of fields to join to this column.


            -  **fit_field** :index:`: <pair: output - kibom - options - conf; fit_field>` [string='Config'] Field name used to determine if a particular part is to be fitted (also DNC and variants).
            -  **group_fields** :index:`: <pair: output - kibom - options - conf; group_fields>` [list(string)] List of fields used for sorting individual components into groups.
               Components which match (comparing *all* fields) will be grouped together.
               Field names are case-insensitive.
               If empty: ['Part', 'Part Lib', 'Value', 'Footprint', 'Footprint Lib'] is used.

            -  **ignore_dnf** :index:`: <pair: output - kibom - options - conf; ignore_dnf>` [boolean=true] Exclude DNF (Do Not Fit) components.
            -  **number_rows** :index:`: <pair: output - kibom - options - conf; number_rows>` [boolean=true] First column is the row number.
            -  ``component_aliases`` :index:`: <pair: output - kibom - options - conf; component_aliases>` [list(list(string))] A series of values which are considered to be equivalent for the part name.
               Each entry is a list of equivalen names. Example: ['c', 'c_small', 'cap' ]
               will ensure the equivalent capacitor symbols can be grouped together.
               If empty the following aliases are used:

               - ['r', 'r_small', 'res', 'resistor']
               - ['l', 'l_small', 'inductor']
               - ['c', 'c_small', 'cap', 'capacitor']
               - ['sw', 'switch']
               - ['zener', 'zenersmall']
               - ['d', 'diode', 'd_small'].

            -  ``datasheet_as_link`` :index:`: <pair: output - kibom - options - conf; datasheet_as_link>` [string=''] Column with links to the datasheet (HTML only).
            -  ``digikey_link`` :index:`: <pair: output - kibom - options - conf; digikey_link>` [string|list(string)=''] Column/s containing Digi-Key part numbers, will be linked to web page (HTML only).

            -  ``exclude_any`` :index:`: <pair: output - kibom - options - conf; exclude_any>` [list(dict)] A series of regular expressions used to exclude parts.
               If a component matches ANY of these, it will be excluded.
               Column names are case-insensitive.
               If empty the following list is used:

               - column: References |br|
                 regex: '^TP[0-9]*'
               - column: References |br|
                 regex: '^FID'
               - column: Part |br|
                 regex: 'mount.*hole'
               - column: Part |br|
                 regex: 'solder.*bridge'
               - column: Part |br|
                 regex: 'test.*point'
               - column: Footprint |br|
                 regex 'test.*point'
               - column: Footprint |br|
                 regex: 'mount.*hole'
               - column: Footprint |br|
                 regex: 'fiducial'.

               -  Valid keys:

                  -  ``column`` :index:`: <pair: output - kibom - options - conf - exclude_any; column>` [string=''] Name of the column to apply the regular expression.
                     Use `_field_lcsc_part` to get the value defined in the global options.
                  -  *field* :index:`: <pair: output - kibom - options - conf - exclude_any; field>` Alias for column.
                  -  ``regex`` :index:`: <pair: output - kibom - options - conf - exclude_any; regex>` [string=''] Regular expression to match.
                  -  *regexp* :index:`: <pair: output - kibom - options - conf - exclude_any; regexp>` Alias for regex.

            -  ``group_connectors`` :index:`: <pair: output - kibom - options - conf; group_connectors>` [boolean=true] Connectors with the same footprints will be grouped together, independent of the name of the connector.
            -  ``hide_headers`` :index:`: <pair: output - kibom - options - conf; hide_headers>` [boolean=false] Hide column headers.
            -  ``hide_pcb_info`` :index:`: <pair: output - kibom - options - conf; hide_pcb_info>` [boolean=false] Hide project information.
            -  ``html_generate_dnf`` :index:`: <pair: output - kibom - options - conf; html_generate_dnf>` [boolean=true] Generate a separated section for DNF (Do Not Fit) components (HTML only).
            -  ``include_only`` :index:`: <pair: output - kibom - options - conf; include_only>` [list(dict)] A series of regular expressions used to select included parts.
               If there are any regex defined here, only components that match against ANY of them will be included.
               Column names are case-insensitive.
               If empty all the components are included.

               -  Valid keys:

                  -  ``column`` :index:`: <pair: output - kibom - options - conf - include_only; column>` [string=''] Name of the column to apply the regular expression.
                     Use `_field_lcsc_part` to get the value defined in the global options.
                  -  *field* :index:`: <pair: output - kibom - options - conf - include_only; field>` Alias for column.
                  -  ``regex`` :index:`: <pair: output - kibom - options - conf - include_only; regex>` [string=''] Regular expression to match.
                  -  *regexp* :index:`: <pair: output - kibom - options - conf - include_only; regexp>` Alias for regex.

            -  ``merge_blank_fields`` :index:`: <pair: output - kibom - options - conf; merge_blank_fields>` [boolean=true] Component groups with blank fields will be merged into the most compatible group, where possible.
            -  ``mouser_link`` :index:`: <pair: output - kibom - options - conf; mouser_link>` [string|list(string)=''] Column/s containing Mouser part numbers, will be linked to web page (HTML only).

            -  ``ref_separator`` :index:`: <pair: output - kibom - options - conf; ref_separator>` [string=' '] Separator used for the list of references.
            -  ``test_regex`` :index:`: <pair: output - kibom - options - conf; test_regex>` [boolean=true] Each component group will be tested against a number of regular-expressions.
            -  ``use_alt`` :index:`: <pair: output - kibom - options - conf; use_alt>` [boolean=false] Print grouped references in the alternate compressed style eg: R1-R7,R18.

      -  ``separator`` :index:`: <pair: output - kibom - options; separator>` [string=','] CSV Separator.
      -  ``variant`` :index:`: <pair: output - kibom - options; variant>` [string=''] Board variant(s), used to determine which components
         are output to the BoM. To specify multiple variants,
         with a BOM file exported for each variant, separate
         variants with the ';' (semicolon) character.
         This isn't related to the KiBot concept of variants.

-  **type** :index:`: <pair: output - kibom; type>` 'kibom'
-  ``category`` :index:`: <pair: output - kibom; category>` [string|list(string)=''] The category for this output. If not specified an internally defined category is used.
   Categories looks like file system paths, i.e. **PCB/fabrication/gerber**.
   The categories are currently used for `navigate_results`.

-  ``disable_run_by_default`` :index:`: <pair: output - kibom; disable_run_by_default>` [string|boolean] Use it to disable the `run_by_default` status of other output.
   Useful when this output extends another and you don't want to generate the original.
   Use the boolean true value to disable the output you are extending.
-  ``extends`` :index:`: <pair: output - kibom; extends>` [string=''] Copy the `options` section from the indicated output.
   Used to inherit options from another output of the same type.
-  ``groups`` :index:`: <pair: output - kibom; groups>` [string|list(string)=''] One or more groups to add this output. In order to catch typos
   we recommend to add outputs only to existing groups. You can create an empty group if
   needed.

-  ``output_id`` :index:`: <pair: output - kibom; output_id>` [string=''] Text to use for the %I expansion content. To differentiate variations of this output.
-  ``priority`` :index:`: <pair: output - kibom; priority>` [number=50] [0,100] Priority for this output. High priority outputs are created first.
   Internally we use 10 for low priority, 90 for high priority and 50 for most outputs.
-  ``run_by_default`` :index:`: <pair: output - kibom; run_by_default>` [boolean=true] When enabled this output will be created when no specific outputs are requested.

