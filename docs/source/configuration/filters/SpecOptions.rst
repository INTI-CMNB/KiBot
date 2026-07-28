.. _SpecOptions_fi:

:orphan:


SpecOptions parameters
~~~~~~~~~~~~~~~~~~~~~~


.. _SpecOptions_field:

-  **field** :index:`: <pair: filter - spec_to_field - specs; field>` [:ref:`string <string>`] (default: ``''``) Name of the destination field.

.. _SpecOptions_spec:

-  **spec** :index:`: <pair: filter - spec_to_field - specs; spec>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] Name/s of the source spec/s.
   The following names are uniform across distributors: '_desc', '_value', '_tolerance', '_footprint',
   '_power', '_current', '_voltage', '_frequency', '_temp_coeff', '_manf' and '_size'.


.. _SpecOptions_collision:

-  ``collision`` :index:`: <pair: filter - spec_to_field - specs; collision>` [:ref:`string <string>`] (default: ``'warning'``) (choices: "warning", "error", "ignore") How to report a collision between the current value and the new value.

.. _SpecOptions_policy:

-  ``policy`` :index:`: <pair: filter - spec_to_field - specs; policy>` [:ref:`string <string>`] (default: ``'overwrite'``) (choices: "overwrite", "update", "new") Controls the behavior of the copy mechanism.
   `overwrite` always copy the spec value,
   `update` copy only if the field already exist,
   `new` copy only if the field doesn't exist. |br|.

.. _SpecOptions_type:

-  **type** :index:`: <pair: filter - spec_to_field - specs; type>` ''

