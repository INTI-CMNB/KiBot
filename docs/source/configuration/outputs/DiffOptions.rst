.. _DiffOptions:


DiffOptions parameters
~~~~~~~~~~~~~~~~~~~~~~

-  **output** :index:`: <pair: output - diff - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=diff_pcb/diff_sch, %x=pdf). Affected by global options.
-  ``add_link_id`` :index:`: <pair: output - diff - options; add_link_id>` [:ref:`boolean <boolean>`] (default: ``false``) When enabled we create a symlink to the output file with a name that contains the
   git hashes involved in the comparison. If you plan to compress the output don't
   forget to disable the `follow_links` option.
-  ``always_fail_if_missing`` :index:`: <pair: output - diff - options; always_fail_if_missing>` [:ref:`boolean <boolean>`] (default: ``false``) Always fail if the old/new file doesn't exist. Currently we don't fail if they are from a repo.
   So if you refer to a repo point where the file wasn't created KiBot will use an empty file. |br|
   Enabling this option KiBot will report an error.
-  ``cache_dir`` :index:`: <pair: output - diff - options; cache_dir>` [:ref:`string <string>`] (default: ``''``) Directory to cache the intermediate files. Leave it blank to disable the cache.
-  ``color_added`` :index:`: <pair: output - diff - options; color_added>` [:ref:`string <string>`] (default: ``'#00FF00'``) Color used for the added stuff in the '2color' mode.
-  ``color_removed`` :index:`: <pair: output - diff - options; color_removed>` [:ref:`string <string>`] (default: ``'#FF0000'``) Color used for the removed stuff in the '2color' mode.
-  ``copy_instead_of_link`` :index:`: <pair: output - diff - options; copy_instead_of_link>` [:ref:`boolean <boolean>`] (default: ``false``) Modifies the behavior of `add_link_id` to create a copy of the file instead of a
   symlink. Useful for some Windows setups.
-  ``diff_mode`` :index:`: <pair: output - diff - options; diff_mode>` [:ref:`string <string>`] (default: ``'red_green'``) (choices: "red_green", "stats", "2color") In the `red_green` mode added stuff is green and red when removed.
   The `stats` mode is used to measure the amount of difference. In this mode all
   changes are red, but you can abort if the difference is bigger than certain threshold. |br|
   The '2color' mode is like 'red_green', but you can customize the colors.
-  ``dnf_filter`` :index:`: <pair: output - diff - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``dpi`` :index:`: <pair: output - diff - options; dpi>` [:ref:`number <number>`] (default: ``150``) (range: 72 to 600) Resolution (Dots Per Inch) for the diff images.
   Be careful to flush any cached images if you change it. |br|
   Also be careful with the values, images can become huge.
-  ``exclude_filter`` :index:`: <pair: output - diff - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``force_checkout`` :index:`: <pair: output - diff - options; force_checkout>` [:ref:`boolean <boolean>`] (default: ``false``) When `old_type` and/or `new_type` are `git` KiBot will checkout the indicated point.
   Before doing it KiBot will stash any change. Under some circumstances git could fail
   to do a checkout, even after stashing, this option can workaround the problem. |br|
   Note that using it you could potentially lose modified files. For more information
   read https://stackoverflow.com/questions/1248029/git-pull-error-entry-foo-not-uptodate-cannot-merge.
-  ``fuzz`` :index:`: <pair: output - diff - options; fuzz>` [:ref:`number <number>`] (default: ``5``) (range: 0 to 100) Color tolerance (fuzzyness) for the `stats` mode.
-  ``new`` :index:`: <pair: output - diff - options; new>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] The file you want to compare. Leave it blank for the current PCB/SCH.
   A list is accepted only for the `multivar` type. Consult the `old` option for more information.
-  ``new_type`` :index:`: <pair: output - diff - options; new_type>` [:ref:`string <string>`] (default: ``'current'``) (choices: "git", "file", "output", "multivar", "current") How to interpret the `new` name. Use `git` for a git hash, branch, etc.
   Use `current` for the currently loaded PCB/Schematic. |br|
   Use `file` for a file name. Use `output` to specify the name of a `pcb_variant`/`sch_variant` output. |br|
   Use `multivar` to compare a set of variants, in this mode `new` is the list of outputs for the variants. |br|
   This is an extension of the `output` mode. |br|
   If `old` is also `multivar` then it becomes the reference, otherwise we compare using pairs of variants.
-  ``old`` :index:`: <pair: output - diff - options; old>` [:ref:`string <string>`] (default: ``'HEAD'``) Reference file. When using git use `HEAD` to refer to the last commit.
   Use `HEAD~` to refer the previous to the last commit. |br|
   As `HEAD` is for the whole repo you can use `KIBOT_LAST-n` to make
   reference to the changes in the PCB/SCH. The `n` value is how many
   changes in the history you want to go back. A 0 is the same as `HEAD`,
   a 1 means the last time the PCB/SCH was changed, etc. |br|
   Use `KIBOT_TAG-n` to search for the last tag skipping `n` tags. |br|

.. note::
      when using the `checkout` GitHub action you just get the
                   last commit. To clone the full repo use `fetch-depth: '0'`. |br|
..

-  ``old_type`` :index:`: <pair: output - diff - options; old_type>` [:ref:`string <string>`] (default: ``'git'``) (choices: "git", "file", "output", "multivar") How to interpret the `old` name. Use `git` for a git hash, branch, etc.
   Use `file` for a file name. Use `output` to specify the name of a `pcb_variant`/`sch_variant` output. |br|
   Use `multivar` to specify a reference file when `new_type` is also `multivar`.
-  ``only_different`` :index:`: <pair: output - diff - options; only_different>` [:ref:`boolean <boolean>`] (default: ``false``) Only include the pages with differences in the output PDF.
   Note that when no differences are found we get a page saying *No diff*.
-  ``only_first_sch_page`` :index:`: <pair: output - diff - options; only_first_sch_page>` [:ref:`boolean <boolean>`] (default: ``false``) Compare only the main schematic page (root page).
   
.. warning::
   Make sure this page is the page **1** of your schematic.
..

-  ``pcb`` :index:`: <pair: output - diff - options; pcb>` [:ref:`boolean <boolean>`] (default: ``true``) Compare the PCB, otherwise compare the schematic.
-  ``pre_transform`` :index:`: <pair: output - diff - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``threshold`` :index:`: <pair: output - diff - options; threshold>` [:ref:`number <number>`] (default: ``0``) (range: 0 to 1000000) Error threshold for the `stats` mode, 0 is no error. When specified a
   difference bigger than the indicated value will make the diff fail. |br|
   KiBot will return error level 29 and the diff generation will be aborted.
-  ``use_file_id`` :index:`: <pair: output - diff - options; use_file_id>` [:ref:`boolean <boolean>`] (default: ``false``) When creating the link name of an output file related to a variant use the variant
   `file_id` instead of its name.
-  ``variant`` :index:`: <pair: output - diff - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
-  ``zones`` :index:`: <pair: output - diff - options; zones>` [:ref:`string <string>`] (default: ``'global'``) (choices: "global", "fill", "unfill", "none") How to handle PCB zones. The default is *global* and means that we
   fill zones if the *check_zone_fills* preflight is enabled. The *fill* option always forces
   a refill, *unfill* forces a zone removal and *none* lets the zones unchanged. |br|
   Be careful with the cache when changing this setting.

