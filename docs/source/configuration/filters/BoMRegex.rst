.. _BoMRegex_fi:

:orphan:


BoMRegex parameters
~~~~~~~~~~~~~~~~~~~


.. _BoMRegex_column:

-  ``column`` :index:`: <pair: filter - generic - include_only; column>` [:ref:`string <string>`] (default: ``''``) Name of the column to apply the regular expression.
   Use `_field_lcsc_part` to get the value defined in the global options.

.. _BoMRegex_field:

-  *field* :index:`: <pair: filter - generic - include_only; field>` Alias for column.

.. _BoMRegex_invert:

-  ``invert`` :index:`: <pair: filter - generic - include_only; invert>` [:ref:`boolean <boolean>`] (default: ``false``) Invert the regex match result.

.. _BoMRegex_match_if_field:

-  ``match_if_field`` :index:`: <pair: filter - generic - include_only; match_if_field>` [:ref:`boolean <boolean>`] (default: ``false``) Match if the field exists, no regex applied. Not affected by `invert`.

.. _BoMRegex_match_if_no_field:

-  ``match_if_no_field`` :index:`: <pair: filter - generic - include_only; match_if_no_field>` [:ref:`boolean <boolean>`] (default: ``false``) Match if the field doesn't exists, no regex applied. Not affected by `invert`.

.. _BoMRegex_regex:

-  ``regex`` :index:`: <pair: filter - generic - include_only; regex>` [:ref:`string <string>`] (default: ``''``) Regular expression to match.

.. _BoMRegex_regexp:

-  *regexp* :index:`: <pair: filter - generic - include_only; regexp>` Alias for regex.

.. _BoMRegex_skip_if_no_field:

-  ``skip_if_no_field`` :index:`: <pair: filter - generic - include_only; skip_if_no_field>` [:ref:`boolean <boolean>`] (default: ``false``) Skip this test if the field doesn't exist.

