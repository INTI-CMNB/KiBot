.. _KiCadVariable_pre:

:orphan:


KiCadVariable parameters
~~~~~~~~~~~~~~~~~~~~~~~~


.. _KiCadVariable_after:

-  ``after`` :index:`: <pair: preflight - set_text_variables - set_text_variables; after>` [:ref:`string <string>`] (default: ``''``) Text to add after the output of `command`.

.. _KiCadVariable_before:

-  ``before`` :index:`: <pair: preflight - set_text_variables - set_text_variables; before>` [:ref:`string <string>`] (default: ``''``) Text to add before the output of `command`.

.. _KiCadVariable_command:

-  ``command`` :index:`: <pair: preflight - set_text_variables - set_text_variables; command>` [:ref:`string <string>`] (default: ``''``) Command to execute to get the text, will be used only if `text` is empty.
   This command will be executed using the Bash shell. |br|
   Be careful about spaces in file names (i.e. use quotes like this "$KIBOT_PCB_NAME"). |br|
   The `KIBOT_PCB_NAME` environment variable is the PCB file and the
   `KIBOT_SCH_NAME` environment variable is the schematic file.

.. _KiCadVariable_expand_in_command:

-  ``expand_in_command`` :index:`: <pair: preflight - set_text_variables - set_text_variables; expand_in_command>` [:ref:`boolean <boolean>`] (default: ``false``) Expand %X patterns in the command. The context is `schematic`.

.. _KiCadVariable_expand_kibot_patterns:

-  ``expand_kibot_patterns`` :index:`: <pair: preflight - set_text_variables - set_text_variables; expand_kibot_patterns>` [:ref:`boolean <boolean>`] (default: ``true``) Expand %X patterns in the value to assign to the variable. The context is `schematic`.

.. _KiCadVariable_name:

-  ``name`` :index:`: <pair: preflight - set_text_variables - set_text_variables; name>` [:ref:`string <string>`] (default: ``''``) Name of the variable. The `version` variable will be expanded using `${version}`.

.. _KiCadVariable_text:

-  ``text`` :index:`: <pair: preflight - set_text_variables - set_text_variables; text>` [:ref:`string <string>`] (default: ``''``) Text to insert instead of the variable.

.. _KiCadVariable_variable:

-  *variable* :index:`: <pair: preflight - set_text_variables - set_text_variables; variable>` Alias for name.

