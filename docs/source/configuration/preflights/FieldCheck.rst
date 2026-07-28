.. _FieldCheck_pre:

:orphan:


FieldCheck parameters
~~~~~~~~~~~~~~~~~~~~~


.. _FieldCheck_field:

-  **field** :index:`: <pair: preflight - check_fields - check_fields; field>` [:ref:`string <string>`] (default: ``''``) Name of field to check.
   The `*` name is a special case. Is used to check for extra fields. In this case you must have a
   rule for each allowed field name and then a rule containing `*` as name. The `severity_missing`
   is applied if the component contains extra fields.

.. _FieldCheck_regex:

-  **regex** :index:`: <pair: preflight - check_fields - check_fields; regex>` [:ref:`string <string>`] (default: ``''``) Regular expression to match the field content. Note that technically we do a search, not a match.

.. _FieldCheck_regexp:

-  *regexp* :index:`: <pair: preflight - check_fields - check_fields; regexp>` Alias for regex.

.. _FieldCheck_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: preflight - check_fields - check_fields; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.


.. _FieldCheck_numeric_condition:

-  ``numeric_condition`` :index:`: <pair: preflight - check_fields - check_fields; numeric_condition>` [:ref:`string <string>`] (default: ``'none'``) (choices: ">", ">=", "<", "<=", "=", "none") Convert the group 1 of the regular expression to a number and apply this operation
   to the *numeric_reference* value.

.. _FieldCheck_numeric_reference:

-  ``numeric_reference`` :index:`: <pair: preflight - check_fields - check_fields; numeric_reference>` [:ref:`number <number>`] (default: ``0``) Value to compare using *numeric_condition*.

.. _FieldCheck_severity:

-  ``severity`` :index:`: <pair: preflight - check_fields - check_fields; severity>` [:ref:`string <string>`] (default: ``'error'``) (choices: "error", "warning", "info", "skip", "continue") Default severity applied to various situations.
   The *error* will stop execution. |br|
   The *warning* and *info* will generate a message and continue with the rest of the tests. |br|
   In the *skip* case we jump to the next component. |br|
   Use *continue* to just skip this test and apply the rest.

.. _FieldCheck_severity_fail_condition:

-  ``severity_fail_condition`` :index:`: <pair: preflight - check_fields - check_fields; severity_fail_condition>` [:ref:`string <string>`] (default: ``'default'``) (choices: "error", "warning", "info", "skip", "continue", "default") What to do when the *numeric_condition* isn't met.
   Default means to use the *severity* option.

.. _FieldCheck_severity_missing:

-  ``severity_missing`` :index:`: <pair: preflight - check_fields - check_fields; severity_missing>` [:ref:`string <string>`] (default: ``'continue'``) (choices: "error", "warning", "info", "skip", "continue", "default") What to do if the field isn't defined.
   Default means to use the *severity* option.

.. _FieldCheck_severity_no_match:

-  ``severity_no_match`` :index:`: <pair: preflight - check_fields - check_fields; severity_no_match>` [:ref:`string <string>`] (default: ``'default'``) (choices: "error", "warning", "info", "skip", "continue", "default") What to do when the regex doesn't match.
   Default means to use the *severity* option.

.. _FieldCheck_severity_no_number:

-  ``severity_no_number`` :index:`: <pair: preflight - check_fields - check_fields; severity_no_number>` [:ref:`string <string>`] (default: ``'default'``) (choices: "error", "warning", "info", "skip", "continue", "default") What to do if we don't get a number for a *numeric_condition*.
   Default means to use the *severity* option.

