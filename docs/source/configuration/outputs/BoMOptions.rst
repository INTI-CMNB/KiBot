.. _BoMOptions:

:orphan:


BoMOptions parameters
~~~~~~~~~~~~~~~~~~~~~


.. _BoMOptions_columns:

-  **columns** :index:`: <pair: output - bom - options; columns>`  [:ref:`BoMColumns parameters <BoMColumns>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>`] (default: computed for your project) List of columns to display.
   One entry can be just the name of the field (a string). |br|
   If you want to import the columns used in KiCad internal BoM tool add an entry `_kicad_bom_fields`,
   this will be replaced by the list from KiCad. |br|
   In addition to all user defined fields you have various special columns, consult :ref:`bom_columns`.

.. _BoMOptions_csv:

-  **csv** :index:`: <pair: output - bom - options; csv>`  [:ref:`BoMCSV parameters <BoMCSV>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options for the CSV, TXT and TSV formats.

.. _BoMOptions_format:

-  **format** :index:`: <pair: output - bom - options; format>` [:ref:`string <string>`] (default: ``'Auto'``) (choices: "HTML", "CSV", "TXT", "TSV", "XML", "XLSX", "HRTXT", "KICAD", "JSON", "Auto") format for the BoM.
   `Auto` defaults to CSV or a guess according to the options. |br|
   HRTXT stands for Human Readable TeXT. |br|
   KICAD is used to get the options from KiCad project. In KiCad you can configure CSV like options.

.. _BoMOptions_group_fields:

-  **group_fields** :index:`: <pair: output - bom - options; group_fields>` [:ref:`list(string) <list(string)>`] (default: ``['part', 'part lib', 'value', 'footprint', 'footprint lib', 'voltage', 'tolerance', 'current', 'power']``) [:ref:`case insensitive <no_case>`]List of fields used for sorting individual components into groups.
   Components which match (comparing *all* fields) will be grouped together. |br|
   Field names are case-insensitive. |br|
   For empty fields the behavior is defined by the `group_fields_fallbacks`, `merge_blank_fields` and
   `merge_both_blank` options. |br|
   Note that for resistors, capacitors and inductors the _Value_ field is parsed and qualifiers, like
   tolerance, are discarded. Please use a separated field and disable `merge_blank_fields` if this
   information is important. You can also disable `parse_value`. |br|
   When using `_kicad_bom_fields` in the `columns` you should use `[]` for this value, so the fields
   selected in KiCad are used. |br|
   Note that when user defined fields are different we merge the fields using `sep_for_merged`. Also
   note that you can merge different `Value` fields using `merge_values`. |br|
   If empty: ['Part', 'Part Lib', 'Value', 'Footprint', 'Footprint Lib',
   'Voltage', 'Tolerance', 'Current', 'Power'] is used.


.. _BoMOptions_hrtxt:

-  **hrtxt** :index:`: <pair: output - bom - options; hrtxt>`  [:ref:`BoMTXT parameters <BoMTXT>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options for the HRTXT format.

.. _BoMOptions_html:

-  **html** :index:`: <pair: output - bom - options; html>`  [:ref:`BoMHTML parameters <BoMHTML>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options for the HTML format.

.. _BoMOptions_ignore_dnf:

-  **ignore_dnf** :index:`: <pair: output - bom - options; ignore_dnf>` [:ref:`boolean <boolean>`] (default: ``true``) Exclude DNF (Do Not Fit) components.

.. _BoMOptions_json:

-  **json** :index:`: <pair: output - bom - options; json>`  [:ref:`BoMLinkableSimple parameters <BoMLinkableSimple>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options for the JSON format.

.. _BoMOptions_normalize_values:

-  **normalize_values** :index:`: <pair: output - bom - options; normalize_values>` [:ref:`boolean <boolean>`] (default: ``false``) Try to normalize the R, L and C values, producing uniform units and prefixes.

.. _BoMOptions_number:

-  **number** :index:`: <pair: output - bom - options; number>` [:ref:`number <number>`] (default: ``1``) Number of boards to build (components multiplier).

.. _BoMOptions_output:

-  **output** :index:`: <pair: output - bom - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) filename for the output (%i=bom). The extension depends on the selected format.
   In the case of the **KICAD** format the extension comes from the name you selected in KiCad's
   internal BoM. Affected by global options.

.. _BoMOptions_sort_style:

-  **sort_style** :index:`: <pair: output - bom - options; sort_style>` [:ref:`string <string>`] (default: ``'type_value'``) (choices: "type_value", "type_value_ref", "ref", "kicad_bom", "field") Sorting criteria.

   - type_value: component kind (reference prefix), then by value
   - type_value_ref: like *type_value* but use the reference when we don't have a value
   - ref: by reference
   - kicad_bom: according to the options of the KiCad BoM tool
   - field: using the `sort_field` field/s.

.. _BoMOptions_units:

-  **units** :index:`: <pair: output - bom - options; units>` [:ref:`string <string>`] (default: ``'millimeters'``) (choices: "millimeters", "inches", "mils") Units used for the positions ('Footprint X', 'Footprint Y', 'Footprint X-Size' and
   'Footprint Y-Size' columns). |br|
   Affected by global options.

.. _BoMOptions_xlsx:

-  **xlsx** :index:`: <pair: output - bom - options; xlsx>`  [:ref:`BoMXLSX parameters <BoMXLSX>`] [:ref:`dict <dict>`] (default: empty dict, default values used) Options for the XLSX format.

.. _BoMOptions_aggregate:

-  ``aggregate`` :index:`: <pair: output - bom - options; aggregate>`  [:ref:`Aggregate parameters <Aggregate>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Add components from other projects.
   You can use CSV files, the first row must contain the names of the fields. |br|
   The `Reference` and `Value` are mandatory, in most cases `Part` is also needed. |br|
   The `Part` column should contain the name/type of the component. This is important for
   passive components (R, L, C, etc.). If this information isn't available consider
   configuring the grouping to exclude the `Part`.

.. _BoMOptions_angle_positive:

-  ``angle_positive`` :index:`: <pair: output - bom - options; angle_positive>` [:ref:`boolean <boolean>`] (default: ``true``) Always use positive values for the footprint rotation.

.. _BoMOptions_bottom_negative_x:

-  ``bottom_negative_x`` :index:`: <pair: output - bom - options; bottom_negative_x>` [:ref:`boolean <boolean>`] (default: ``false``) Use negative X coordinates for footprints on bottom layer (for XYRS).

.. _BoMOptions_component_aliases:

-  ``component_aliases`` :index:`: <pair: output - bom - options; component_aliases>` [:ref:`list(list(string)) <list(list(string))>`] (default: ``[['r', 'r_small', 'res', 'resistor'], ['l', 'l_small', 'inductor'], ['c', 'c_small', 'cap', 'capacitor'], ['sw', 'switch'], ['zener', 'zenersmall'], ['d', 'diode', 'd_small']]``) A series of values which are considered to be equivalent for the part name.
   Each entry is a list of equivalen names. Example: ['c', 'c_small', 'cap' ]
   will ensure the equivalent capacitor symbols can be grouped together. |br|
   If empty the following aliases are used:

   - ['r', 'r_small', 'res', 'resistor']
   - ['l', 'l_small', 'inductor']
   - ['c', 'c_small', 'cap', 'capacitor']
   - ['sw', 'switch']
   - ['zener', 'zenersmall']
   - ['d', 'diode', 'd_small'].


.. _BoMOptions_cost_extra_columns:

-  ``cost_extra_columns`` :index:`: <pair: output - bom - options; cost_extra_columns>`  [:ref:`BoMColumns parameters <BoMColumns>`] [:ref:`list(dict) <list(dict)>` | :ref:`list(string) <list(string)>`] (default: ``[]``) List of columns to add to the global section of the cost.
   Can be just the name of the field.

.. _BoMOptions_count_smd_tht:

-  ``count_smd_tht`` :index:`: <pair: output - bom - options; count_smd_tht>` [:ref:`boolean <boolean>`] (default: ``false``) Show the stats about how many of the components are SMD/THT. You must provide the PCB.

.. _BoMOptions_distributors:

-  ``distributors`` :index:`: <pair: output - bom - options; distributors>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``[]``) [:ref:`comma separated <comma_sep>`] Include this distributors list. Default is all the available.


.. _BoMOptions_dnc_filter:

-  ``dnc_filter`` :index:`: <pair: output - bom - options; dnc_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_kibom_dnc_CONFIG_FIELD'``) Name of the filter to mark components as 'Do Not Change'.
   The default filter marks components with a DNC value or DNC in the Config field. |br|
   This option is for simple cases, consider using a full variant for complex cases.


.. _BoMOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - bom - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_kibom_dnf_CONFIG_FIELD'``) Name of the filter to mark components as 'Do Not Fit'.
   The default filter marks components with a DNF value or DNF in the Config field. |br|
   When using KiCad variants the default is '_null'. |br|
   This option is for simple cases, consider using a full variant for complex cases.


.. _BoMOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - bom - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_mechanical'``) Name of the filter to exclude components from BoM processing.
   The default filter (built-in filter '_mechanical') excludes test points, fiducial marks, mounting holes, etc. |br|
   When using KiCad variants the default is '_null'. |br|
   Please consult the built-in filters explanation to fully understand what is excluded by default. |br|
   This option is for simple cases, consider using a full variant for complex cases.


.. _BoMOptions_exclude_marked_in_pcb:

-  ``exclude_marked_in_pcb`` :index:`: <pair: output - bom - options; exclude_marked_in_pcb>` [:ref:`boolean <boolean>`] (default: ``false``) Exclude components marked with *Exclude from BOM* in the PCB.
   This is a KiCad 6 option.

.. _BoMOptions_exclude_marked_in_sch:

-  ``exclude_marked_in_sch`` :index:`: <pair: output - bom - options; exclude_marked_in_sch>` [:ref:`boolean <boolean>`] (default: ``true``) Exclude components marked with *Exclude from bill of materials* in the schematic.
   This is a KiCad 6 option.

.. _BoMOptions_expand_text_vars:

-  ``expand_text_vars`` :index:`: <pair: output - bom - options; expand_text_vars>` [:ref:`boolean <boolean>`] (default: ``true``) Expand KiCad 6 text variables after applying all filters and variants.
   This is done using a **_expand_text_vars** filter. |br|
   If you need to customize the filter, or apply it before, you can disable this option and
   add a custom filter to the filter chain.

.. _BoMOptions_fit_field:

-  ``fit_field`` :index:`: <pair: output - bom - options; fit_field>` [:ref:`string <string>`] (default: ``'config'``) [:ref:`case insensitive <no_case>`]Field name used for internal filters (not for variants).

.. _BoMOptions_footprint_populate_values:

-  ``footprint_populate_values`` :index:`: <pair: output - bom - options; footprint_populate_values>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'no,yes'``) [:ref:`comma separated <comma_sep>`] (must contain 2 elements) Values for the `Footprint Populate` column.


.. _BoMOptions_footprint_type_values:

-  ``footprint_type_values`` :index:`: <pair: output - bom - options; footprint_type_values>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'SMD,THT,VIRTUAL'``) [:ref:`comma separated <comma_sep>`] (must contain 3 elements) Values for the `Footprint Type` column.


.. _BoMOptions_group_connectors:

-  ``group_connectors`` :index:`: <pair: output - bom - options; group_connectors>` [:ref:`boolean <boolean>`] (default: ``true``) Connectors with the same footprints will be grouped together, independent of the name of the connector.
   In order to work the symbol must be from a library containing `connector` in its name.

.. _BoMOptions_group_fields_fallbacks:

-  ``group_fields_fallbacks`` :index:`: <pair: output - bom - options; group_fields_fallbacks>` [:ref:`list(string) <list(string)>`] (default: ``[]``) [:ref:`case insensitive <no_case>`]List of fields to be used when the fields in `group_fields` are empty.
   The first field in this list is the fallback for the first in `group_fields`, and so on.


.. _BoMOptions_group_not_fitted:

-  ``group_not_fitted`` :index:`: <pair: output - bom - options; group_not_fitted>` [:ref:`boolean <boolean>`] (default: ``false``) Enable it to group fitted and not fitted components together. This is how KiCad's internal BoM behaves.

.. _BoMOptions_int_qtys:

-  ``int_qtys`` :index:`: <pair: output - bom - options; int_qtys>` [:ref:`boolean <boolean>`] (default: ``true``) Component quantities are always expressed as integers. Using the ceil() function.

.. _BoMOptions_kicad_dnp_applied:

-  ``kicad_dnp_applied`` :index:`: <pair: output - bom - options; kicad_dnp_applied>` [:ref:`string <string>`] (default: ``'global'``) (choices: "global", "yes", "no") What we do with the KiCad DNP flag.
   `global` means we apply the `kicad_dnp_applied` global option. |br|
   `yes` means we always remove DNP components. |br|
   `no` means we ignore the DNP flag and let filters do its work.

.. _BoMOptions_merge_blank_fields:

-  ``merge_blank_fields`` :index:`: <pair: output - bom - options; merge_blank_fields>` [:ref:`boolean <boolean>`] (default: ``true``) Component groups with blank fields will be merged into the most compatible group, where possible.

.. _BoMOptions_merge_both_blank:

-  ``merge_both_blank`` :index:`: <pair: output - bom - options; merge_both_blank>` [:ref:`boolean <boolean>`] (default: ``true``) When creating groups two components with empty/missing field will be interpreted as with the same value.

.. _BoMOptions_merge_values:

-  ``merge_values`` :index:`: <pair: output - bom - options; merge_values>` [:ref:`boolean <boolean>`] (default: ``false``) Merge the values of different components in a group.
   Used when you abuse the value field, i.e. for connectors where the Value is the connector purpose.

.. _BoMOptions_no_conflict:

-  ``no_conflict`` :index:`: <pair: output - bom - options; no_conflict>` [:ref:`list(string) <list(string)>`] (default: computed for your project) [:ref:`case insensitive <no_case>`]List of fields where we tolerate conflicts.
   Use it to avoid undesired warnings. |br|
   By default the field indicated in `fit_field`, the field used for variants and
   the field `part` are excluded.


.. _BoMOptions_no_distributors:

-  ``no_distributors`` :index:`: <pair: output - bom - options; no_distributors>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``[]``) [:ref:`comma separated <comma_sep>`] Exclude this distributors list.
   They are removed after computing `distributors`.


.. _BoMOptions_normalize_locale:

-  ``normalize_locale`` :index:`: <pair: output - bom - options; normalize_locale>` [:ref:`boolean <boolean>`] (default: ``false``) When normalizing values use the locale decimal point.

.. _BoMOptions_parse_value:

-  ``parse_value`` :index:`: <pair: output - bom - options; parse_value>` [:ref:`boolean <boolean>`] (default: ``true``) Parse the `Value` field so things like *1k* and *1000* are interpreted as equal.
   Note that this implies that *1k 1%* is the same as *1k 5%*. If you really need to group using the
   extra information split it in separated fields, add the fields to `group_fields` and disable
   `merge_blank_fields`.

.. _BoMOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - bom - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   This option is for simple cases, consider using a full variant for complex cases.


.. _BoMOptions_ref_id:

-  ``ref_id`` :index:`: <pair: output - bom - options; ref_id>` [:ref:`string <string>`] (default: ``''``) A prefix to add to all the references from this project. Used for multiple projects.

.. _BoMOptions_ref_range_separator:

-  ``ref_range_separator`` :index:`: <pair: output - bom - options; ref_range_separator>` [:ref:`string <string>`] (default: ``'-'``) Separator used for ranges in the list of references. Used when `use_alt` is enabled.
   Ignored when using the KICAD format.

.. _BoMOptions_ref_separator:

-  ``ref_separator`` :index:`: <pair: output - bom - options; ref_separator>` [:ref:`string <string>`] (default: ``' '``) Separator used for the list of references. Ignored when using the KICAD format.

.. _BoMOptions_right_digits:

-  ``right_digits`` :index:`: <pair: output - bom - options; right_digits>` [:ref:`number <number>`] (default: ``4``) Number of digits for mantissa part of coordinates ('Footprint X', 'Footprint Y', 'Footprint X-Size',
   'Footprint Y-Size' and 'Footprint Rot' columns) (0 is auto).

.. _BoMOptions_sep_for_merged:

-  ``sep_for_merged`` :index:`: <pair: output - bom - options; sep_for_merged>` [:ref:`string <string>`] (default: ``' '``) Text to separate multiple field values of components merged in the same group.

.. _BoMOptions_sort_ascending:

-  ``sort_ascending`` :index:`: <pair: output - bom - options; sort_ascending>` [:ref:`boolean <boolean>`] (default: ``true``) Sort in ascending order.

.. _BoMOptions_sort_field:

-  ``sort_field`` :index:`: <pair: output - bom - options; sort_field>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'Reference'``) [:ref:`case insensitive <no_case>`]Field or fields used for the `field` `sort_style`.


.. _BoMOptions_source_by_id:

-  ``source_by_id`` :index:`: <pair: output - bom - options; source_by_id>` [:ref:`boolean <boolean>`] (default: ``false``) Generate the `Source BoM` column using the reference ID instead of the project name.

.. _BoMOptions_tilde_is_empty:

-  ``tilde_is_empty`` :index:`: <pair: output - bom - options; tilde_is_empty>` [:ref:`boolean <boolean>`] (default: ``true``) Interpret fields that just contains `~` as empty fields.
   But don't mark them as empty in the HTML.

.. _BoMOptions_use_alt:

-  ``use_alt`` :index:`: <pair: output - bom - options; use_alt>` [:ref:`boolean <boolean>`] (default: ``false``) Print grouped references in the alternate compressed style eg: R1-R7,R18.
   Ignored when using the KICAD format.

.. _BoMOptions_use_aux_axis_as_origin:

-  ``use_aux_axis_as_origin`` :index:`: <pair: output - bom - options; use_aux_axis_as_origin>` [:ref:`boolean <boolean>`] (default: ``true``) Use the auxiliary axis as origin for coordinates (KiCad default) (for XYRS).

.. _BoMOptions_use_ref_ranges:

-  *use_ref_ranges* :index:`: <pair: output - bom - options; use_ref_ranges>` Alias for use_alt.

.. _BoMOptions_variant:

-  ``variant`` :index:`: <pair: output - bom - options; variant>` [:ref:`string <string>`] (default: ``'_kibom_simple'``) Board variant, used to determine which components are output to the BoM.
   The `_kibom_simple` variant is a KiBoM variant without any filters and it provides some basic
   compatibility with KiBoM. Note that this output has default filters that behaves like KiBoM. |br|
   The combination between the default for this option and the defaults for the filters provides
   a behavior that mimics KiBoM default behavior. |br|
   If you want to use KiCad 10 variants: use the name of the KiCad 10 variant, `Default` is the
   default variant.

Used dicts
----------

- :ref:`Aggregate parameters <Aggregate>`
- :ref:`BoMCSV parameters <BoMCSV>`
- :ref:`BoMColumns parameters <BoMColumns>`
- :ref:`BoMHTML parameters <BoMHTML>`
- :ref:`BoMLinkableSimple parameters <BoMLinkableSimple>`
- :ref:`BoMTXT parameters <BoMTXT>`
- :ref:`BoMXLSX parameters <BoMXLSX>`
