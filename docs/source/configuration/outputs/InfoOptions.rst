.. _InfoOptions:

:orphan:


InfoOptions parameters
~~~~~~~~~~~~~~~~~~~~~~


.. _InfoOptions_output:

-  **output** :index:`: <pair: output - info - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=info, %x=txt). Affected by global options.

.. _InfoOptions_environment:

-  ``environment`` :index:`: <pair: output - info - options; environment>` [:ref:`string <string>`] (default: ``'names'``) (choices: "names", "none", "full") List environment variables.
   IMPORTANT: Don't use `full` unless you know you are not leaking sensitive information.

