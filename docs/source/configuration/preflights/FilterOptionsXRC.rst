.. _FilterOptionsXRC_pre:

:orphan:


FilterOptionsXRC parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``change_to`` :index:`: <pair: preflight - erc - erc - filters; change_to>` [:ref:`string <string>`] (default: ``'ignore'``) (choices: "error", "warning", "ignore") The action of the filter.
   Changing to *ignore* is the default and is used to suppress a violation, but you can also change
   it to be an *error* or a *warning*. Note that violations excluded by KiCad are also analyzed,
   so you can revert a GUI exclusion.
-  ``error`` :index:`: <pair: preflight - erc - erc - filters; error>` [:ref:`string <string>`] (default: ``''``) Error id we want to exclude.
-  ``filter`` :index:`: <pair: preflight - erc - erc - filters; filter>` [:ref:`string <string>`] (default: ``''``) Name for the filter, for documentation purposes.
-  *filter_msg* :index:`: <pair: preflight - erc - erc - filters; filter_msg>` Alias for filter.
-  ``regex`` :index:`: <pair: preflight - erc - erc - filters; regex>` [:ref:`string <string>`] (default: ``''``) Regular expression to match the text for the error we want to exclude.
-  *regexp* :index:`: <pair: preflight - erc - erc - filters; regexp>` Alias for regex.

