.. _BoMLabelsOptions:

:orphan:


BoMLabelsOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **bom** :index:`: <pair: output - bom_labels - options; bom>` [:ref:`string <string>`] (default: ``''``) BoM output used for the labels.
-  **output** :index:`: <pair: output - bom_labels - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Name for the generated PDF (%i=bom_labels %x=pdf). Affected by global options.
-  ``dnf_filter`` :index:`: <pair: output - bom_labels - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``exclude_filter`` :index:`: <pair: output - bom_labels - options; exclude_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to exclude components from processing.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``font`` :index:`: <pair: output - bom_labels - options; font>` [:ref:`string <string>`] (default: ``'Helvetica-Bold'``) Font used for the labels.
-  ``font_size_header`` :index:`: <pair: output - bom_labels - options; font_size_header>` [:ref:`number <number>`] (default: ``6``) Default size of the header font, will be reduced to fit the text.
-  ``font_size_rest`` :index:`: <pair: output - bom_labels - options; font_size_rest>` [:ref:`number <number>`] (default: ``4``) Default size of the normal font, will be reduced to fit the text.
-  ``header_sep`` :index:`: <pair: output - bom_labels - options; header_sep>` [:ref:`number <number>`] (default: ``3``) Distance from header to first line in mm.
-  ``height`` :index:`: <pair: output - bom_labels - options; height>` [:ref:`number <number>`] (default: ``10``) Label height in mm.
-  ``line_height`` :index:`: <pair: output - bom_labels - options; line_height>` [:ref:`number <number>`] (default: ``1.5``) Regular line height in mm.
-  ``margin_top`` :index:`: <pair: output - bom_labels - options; margin_top>` [:ref:`number <number>`] (default: ``3``) Top margin in mm.
-  ``margin_x`` :index:`: <pair: output - bom_labels - options; margin_x>` [:ref:`number <number>`] (default: ``2``) X margin in mm.
-  ``pre_transform`` :index:`: <pair: output - bom_labels - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   Is a short-cut to use for simple cases where a variant is an overkill. |br|
   Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
   variant.

-  ``rows`` :index:`: <pair: output - bom_labels - options; rows>` [:ref:`number <number>`] (default: ``3``) How many rows we print, including the header.
-  ``variant`` :index:`: <pair: output - bom_labels - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.
-  ``width`` :index:`: <pair: output - bom_labels - options; width>` [:ref:`number <number>`] (default: ``20``) Label width in mm.

