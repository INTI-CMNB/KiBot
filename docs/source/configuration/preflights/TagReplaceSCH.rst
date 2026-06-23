.. _TagReplaceSCH_pre:

:orphan:


TagReplaceSCH parameters
~~~~~~~~~~~~~~~~~~~~~~~~


.. _TagReplaceSCH_after:

-  ``after`` :index:`: <pair: preflight - sch_replace - sch_replace - replace_tags; after>` [:ref:`string <string>`] (default: ``''``) Text to add after the output of `command`.

.. _TagReplaceSCH_before:

-  ``before`` :index:`: <pair: preflight - sch_replace - sch_replace - replace_tags; before>` [:ref:`string <string>`] (default: ``''``) Text to add before the output of `command`.

.. _TagReplaceSCH_command:

-  ``command`` :index:`: <pair: preflight - sch_replace - sch_replace - replace_tags; command>` [:ref:`string <string>`] (default: ``''``) Command to execute to get the text, will be used only if `text` is empty.
   KIBOT_SCH_NAME variable is the name of the current sheet. |br|
   KIBOT_TOP_SCH_NAME variable is the name of the top sheet.

.. _TagReplaceSCH_tag:

-  ``tag`` :index:`: <pair: preflight - sch_replace - sch_replace - replace_tags; tag>` [:ref:`string <string>`] (default: ``''``) Name of the tag to replace. Use `version` for a tag named `@version@`.

.. _TagReplaceSCH_tag_delimiter:

-  ``tag_delimiter`` :index:`: <pair: preflight - sch_replace - sch_replace - replace_tags; tag_delimiter>` [:ref:`string <string>`] (default: ``'@'``) Character used to indicate the beginning and the end of a tag.
   Don't change it unless you really know about KiCad's file formats.

.. _TagReplaceSCH_text:

-  ``text`` :index:`: <pair: preflight - sch_replace - sch_replace - replace_tags; text>` [:ref:`string <string>`] (default: ``''``) Text to insert instead of the tag.

