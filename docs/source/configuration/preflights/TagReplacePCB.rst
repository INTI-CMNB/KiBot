.. _TagReplacePCB_pre:

:orphan:


TagReplacePCB parameters
~~~~~~~~~~~~~~~~~~~~~~~~


.. _TagReplacePCB_after:

-  ``after`` :index:`: <pair: preflight - pcb_replace - pcb_replace - replace_tags; after>` [:ref:`string <string>`] (default: ``''``) Text to add after the output of `command`.

.. _TagReplacePCB_before:

-  ``before`` :index:`: <pair: preflight - pcb_replace - pcb_replace - replace_tags; before>` [:ref:`string <string>`] (default: ``''``) Text to add before the output of `command`.

.. _TagReplacePCB_command:

-  ``command`` :index:`: <pair: preflight - pcb_replace - pcb_replace - replace_tags; command>` [:ref:`string <string>`] (default: ``''``) Command to execute to get the text, will be used only if `text` is empty.
   KIBOT_PCB_NAME variable is the name of the current PCB.

.. _TagReplacePCB_tag:

-  ``tag`` :index:`: <pair: preflight - pcb_replace - pcb_replace - replace_tags; tag>` [:ref:`string <string>`] (default: ``''``) Name of the tag to replace. Use `version` for a tag named `@version@`.

.. _TagReplacePCB_tag_delimiter:

-  ``tag_delimiter`` :index:`: <pair: preflight - pcb_replace - pcb_replace - replace_tags; tag_delimiter>` [:ref:`string <string>`] (default: ``'@'``) Character used to indicate the beginning and the end of a tag.
   Don't change it unless you really know about KiCad's file formats.

.. _TagReplacePCB_text:

-  ``text`` :index:`: <pair: preflight - pcb_replace - pcb_replace - replace_tags; text>` [:ref:`string <string>`] (default: ``''``) Text to insert instead of the tag.

