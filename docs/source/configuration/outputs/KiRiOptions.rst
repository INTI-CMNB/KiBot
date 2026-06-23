.. _KiRiOptions:

:orphan:


KiRiOptions parameters
~~~~~~~~~~~~~~~~~~~~~~


.. _KiRiOptions_color_theme:

-  **color_theme** :index:`: <pair: output - kiri - options; color_theme>` [:ref:`string <string>`] (default: ``'_builtin_classic'``) Selects the color theme. Only applies to KiCad 6.
   To use the KiCad 6 default colors select `_builtin_default`. |br|
   Usually user colors are stored as `user`, but you can give it another name.

.. _KiRiOptions_keep_generated:

-  **keep_generated** :index:`: <pair: output - kiri - options; keep_generated>` [:ref:`boolean <boolean>`] (default: ``false``) Avoid PCB and SCH images regeneration. Useful for incremental usage.

.. _KiRiOptions_background_color:

-  ``background_color`` :index:`: <pair: output - kiri - options; background_color>` [:ref:`string <string>`] (default: ``'#FFFFFF'``) Color used for the background of the diff canvas.

.. _KiRiOptions_dnf_filter:

-  ``dnf_filter`` :index:`: <pair: output - kiri - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _KiRiOptions_exclude_filter:

-  ``exclude_filter`` :index:`: <pair: output - kiri - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _KiRiOptions_max_commits:

-  ``max_commits`` :index:`: <pair: output - kiri - options; max_commits>` [:ref:`number <number>`] (default: ``0``) Maximum number of commits to include. Use 0 for all available commits.

.. _KiRiOptions_pre_transform:

-  ``pre_transform`` :index:`: <pair: output - kiri - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.


.. _KiRiOptions_revision:

-  ``revision`` :index:`: <pair: output - kiri - options; revision>` [:ref:`string <string>`] (default: ``'HEAD'``) Starting point for the commits, can be a branch, a hash, etc.
   Note that this can be a revision-range, consult the gitrevisions manual for more information.

.. _KiRiOptions_variant:

-  ``variant`` :index:`: <pair: output - kiri - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

.. _KiRiOptions_zones:

-  ``zones`` :index:`: <pair: output - kiri - options; zones>` [:ref:`string <string>`] (default: ``'global'``) (choices: "global", "fill", "unfill", "none") How to handle PCB zones. The default is *global* and means that we
   fill zones if the *check_zone_fills* preflight is enabled. The *fill* option always forces
   a refill, *unfill* forces a zone removal and *none* lets the zones unchanged. |br|
   Be careful with the *keep_generated* option when changing this setting.

