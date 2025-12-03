.. _Update_XMLOptions_pre:

:orphan:


Update_XMLOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **check_pcb_parity** :index:`: <pair: preflight - update_xml - update_xml; check_pcb_parity>` [:ref:`boolean <boolean>`] (default: ``false``) Check if the PCB and Schematic are synchronized.
   This is equivalent to the *Test for parity between PCB and schematic* of the DRC dialog. |br|
   Only for KiCad 6 and 7. **Important**: when using KiCad 6 and the *Exclude from BoM* attribute
   these components won't be included in the generated XML, so we can't check its parity.
-  ``as_warnings`` :index:`: <pair: preflight - update_xml - update_xml; as_warnings>` [:ref:`boolean <boolean>`] (default: ``false``) Inform the problems as warnings and don't stop.
-  ``enabled`` :index:`: <pair: preflight - update_xml - update_xml; enabled>` [:ref:`boolean <boolean>`] (default: ``true``) Enable the update. This is the replacement for the boolean value.

