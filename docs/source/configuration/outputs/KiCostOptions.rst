.. _KiCostOptions:

:orphan:


KiCostOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~


.. _KiCostOptions_board_qty:

-  *board_qty* :index:`: <pair: output - kicost - options; board_qty>` Alias for number.

.. _KiCostOptions_currency:

-  **currency** :index:`: <pair: output - kicost - options; currency>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'USD'``) Currency priority. Use ISO4217 codes (i.e. USD, EUR).


.. _KiCostOptions_distributors:

-  **distributors** :index:`: <pair: output - kicost - options; distributors>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``[]``) Include this distributors list. Default is all the available.


.. _KiCostOptions_no_distributors:

-  **no_distributors** :index:`: <pair: output - kicost - options; no_distributors>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``[]``) Exclude this distributors list. They are removed after computing `distributors`.


.. _KiCostOptions_no_price:

-  **no_price** :index:`: <pair: output - kicost - options; no_price>` [:ref:`boolean <boolean>`] (default: ``false``) Do not look for components price. For testing purposes.

.. _KiCostOptions_number:

-  **number** :index:`: <pair: output - kicost - options; number>` [:ref:`number <number>`] (default: ``100``) Number of boards to build (components multiplier).

.. _KiCostOptions_output:

-  **output** :index:`: <pair: output - kicost - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=kicost, %x=xlsx). Affected by global options.

.. _KiCostOptions_aggregate:

-  ``aggregate`` :index:`: <pair: output - kicost - options; aggregate>`  [:ref:`Aggregate parameters <Aggregate>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Add components from other projects.

.. _KiCostOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - kicost - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant. |br|
   Don't use the `kicost_variant` when using internal variants/filters.


.. _KiCostOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - kicost - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _KiCostOptions_fields:

-  ``fields`` :index:`: <pair: output - kicost - options; fields>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``[]``) [:ref:`comma separated <comma_sep>`] List of fields to be added to the global data section.


.. _KiCostOptions_group_fields:

-  ``group_fields`` :index:`: <pair: output - kicost - options; group_fields>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``[]``) [:ref:`comma separated <comma_sep>`] List of fields that can be different for a group.
   Parts with differences in these fields are grouped together, but displayed individually.


.. _KiCostOptions_ignore_fields:

-  ``ignore_fields`` :index:`: <pair: output - kicost - options; ignore_fields>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``[]``) [:ref:`comma separated <comma_sep>`] List of fields to be ignored.


.. _KiCostOptions_kicost_config:

-  ``kicost_config`` :index:`: <pair: output - kicost - options; kicost_config>` [:ref:`string <string>`] (default: ``''``) KiCost configuration file. It contains the keys for the different distributors APIs.
   The regular KiCost config is used when empty. |br|
   Important for CI/CD environments: avoid exposing your API secrets!
   To understand how to achieve this, and also how to make use of the cache please visit the
   `kicost_ci_test <https://github.com/set-soft/kicost_ci_test>`__ repo.

.. _KiCostOptions_kicost_variant:

-  ``kicost_variant`` :index:`: <pair: output - kicost - options; kicost_variant>` [:ref:`string <string>`] (default: ``''``) Regular expression to match the variant field (KiCost option, not internal variants).

.. _KiCostOptions_no_collapse:

-  ``no_collapse`` :index:`: <pair: output - kicost - options; no_collapse>` [:ref:`boolean <boolean>`] (default: ``false``) Do not collapse the part references (collapse=R1-R4).

.. _KiCostOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - kicost - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _KiCostOptions_show_cat_url:

-  ``show_cat_url`` :index:`: <pair: output - kicost - options; show_cat_url>` [:ref:`boolean <boolean>`] (default: ``false``) Include the catalogue links in the catalogue code.

.. _KiCostOptions_split_extra_fields:

-  ``split_extra_fields`` :index:`: <pair: output - kicost - options; split_extra_fields>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``[]``) [:ref:`comma separated <comma_sep>`] Declare part fields to include in multipart split process.


.. _KiCostOptions_translate_fields:

-  ``translate_fields`` :index:`: <pair: output - kicost - options; translate_fields>`  [:ref:`FieldRename parameters <FieldRename>`] [:ref:`list(dict) <list(dict)>`] (default: ``[]``) Fields to rename (KiCost option, not internal filters).

.. _KiCostOptions_variant:

-  ``variant`` :index:`: <pair: output - kicost - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
   Don't use the `kicost_variant` when using internal variants/filters.

Used dicts
----------

- :ref:`Aggregate parameters <Aggregate>`
- :ref:`FieldRename parameters <FieldRename>`
