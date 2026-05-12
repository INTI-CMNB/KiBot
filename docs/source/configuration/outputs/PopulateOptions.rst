.. _PopulateOptions:

:orphan:


PopulateOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **format** :index:`: <pair: output - populate - options; format>` [:ref:`string <string>`] (default: ``'html'``) (choices: "html", "md") Format for the generated output.
-  **input** :index:`: <pair: output - populate - options; input>` [:ref:`string <string>`] (default: ``''``) Name of the input file describing the assembly. Must be a markdown file.
   Note that the YAML section of the file will be skipped, all the needed information
   comes from this output and the `renderer` output, not from the YAML section. |br|
   When empty we use a dummy template, you should provide something better.
-  **renderer** :index:`: <pair: output - populate - options; renderer>` [:ref:`string <string>`] (default: ``''``) Name of the output used to render the PCB steps.
   Currently this must be a `pcbdraw` or `render_3d` output.
-  ``dnf_filter`` :index:`: <pair: output - populate - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - populate - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``imgname`` :index:`: <pair: output - populate - options; imgname>` [:ref:`string <string>`] (default: ``'img/populating_%d.%x'``) Pattern used for the image names. The `%d` is replaced by the image number.
   The `%x` is replaced by the extension. Note that the format is selected by the
   `renderer`.
-  ``initial_components`` :index:`: <pair: output - populate - options; initial_components>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) [:ref:`comma separated <comma_sep>`] List of components soldered before the first step.

-  ``pre_transform`` :index:`: <pair: output - populate - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``template`` :index:`: <pair: output - populate - options; template>` [:ref:`string <string>`] The name of the handlebars template used for the HTML output.
   The extension must be `.handlebars`, it will be added when missing. |br|
   The `simple.handlebars` template is a built-in template.
-  ``variant`` :index:`: <pair: output - populate - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

