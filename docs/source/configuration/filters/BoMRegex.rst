.. _BoMRegex_fi:

:orphan:


BoMRegex parameters
~~~~~~~~~~~~~~~~~~~

-  ``column`` :index:`: <pair: filter - generic - include_only; column>` [:ref:`string <string>`] (default: ``''``) Name of the column to apply the regular expression.
   Use `_field_lcsc_part` to get the value defined in the global options.
-  *field* :index:`: <pair: filter - generic - include_only; field>` Alias for column.
-  ``invert`` :index:`: <pair: filter - generic - include_only; invert>` [:ref:`boolean <boolean>`] (default: ``false``) Invert the regex match result.
-  ``match_if_field`` :index:`: <pair: filter - generic - include_only; match_if_field>` [:ref:`boolean <boolean>`] (default: ``false``) Match if the field exists, no regex applied. Not affected by `invert`.
-  ``match_if_no_field`` :index:`: <pair: filter - generic - include_only; match_if_no_field>` [:ref:`boolean <boolean>`] (default: ``false``) Match if the field doesn't exists, no regex applied. Not affected by `invert`.
-  ``regex`` :index:`: <pair: filter - generic - include_only; regex>` [:ref:`string <string>`] (default: ``''``) Regular expression to match.
-  *regexp* :index:`: <pair: filter - generic - include_only; regexp>` Alias for regex.
-  ``skip_if_no_field`` :index:`: <pair: filter - generic - include_only; skip_if_no_field>` [:ref:`boolean <boolean>`] (default: ``false``) Skip this test if the field doesn't exist.

