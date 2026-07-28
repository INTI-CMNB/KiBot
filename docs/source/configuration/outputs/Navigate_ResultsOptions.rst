.. _Navigate_ResultsOptions:

:orphan:


Navigate_ResultsOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. _Navigate_ResultsOptions_link_from_root:

-  **link_from_root** :index:`: <pair: output - navigate_results - options; link_from_root>` [:ref:`string <string>`] (default: ``''``) The name of a file to create at the main output directory linking to the home page.

.. _Navigate_ResultsOptions_output:

-  **output** :index:`: <pair: output - navigate_results - options; output>` [:ref:`string <string>`] (default: ``'%f-%i%I%v.%x'``) Filename for the output (%i=html, %x=navigate). Affected by global options.

.. _Navigate_ResultsOptions_display_category_images:

-  ``display_category_images`` :index:`: <pair: output - navigate_results - options; display_category_images>` [:ref:`boolean <boolean>`] (default: ``true``) If True, we try to display images for categories according to the category type.

.. _Navigate_ResultsOptions_display_kibot_version:

-  ``display_kibot_version`` :index:`: <pair: output - navigate_results - options; display_kibot_version>` [:ref:`boolean <boolean>`] (default: ``true``) If True, display the KiBot version at the bottom of each page.

.. _Navigate_ResultsOptions_expand_text_vars:

-  ``expand_text_vars`` :index:`: <pair: output - navigate_results - options; expand_text_vars>` [:ref:`boolean <boolean>`] (default: ``true``) Expand KiBot %X and KiCad ${VARIABLE} values in the title.

.. _Navigate_ResultsOptions_header:

-  ``header`` :index:`: <pair: output - navigate_results - options; header>` [:ref:`boolean <boolean>`] (default: ``true``) Add a header containing information for the project.

.. _Navigate_ResultsOptions_image_white_background:

-  ``image_white_background`` :index:`: <pair: output - navigate_results - options; image_white_background>` [:ref:`boolean <boolean>`] (default: ``true``) When creating a miniature preview of a document use a white background instead of a transparent background.
   This helps when using a dark mode.

.. _Navigate_ResultsOptions_logo:

-  ``logo`` :index:`: <pair: output - navigate_results - options; logo>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) PNG file to use as logo, use false to remove.
   The KiBot logo is used by default.


.. _Navigate_ResultsOptions_logo_force_height:

-  ``logo_force_height`` :index:`: <pair: output - navigate_results - options; logo_force_height>` [:ref:`number <number>`] (default: ``-1``) Force logo height in px. Useful to get consistent heights across different logos..

.. _Navigate_ResultsOptions_logo_url:

-  ``logo_url`` :index:`: <pair: output - navigate_results - options; logo_url>` [:ref:`string <string>`] (default: ``'https://github.com/INTI-CMNB/KiBot/'``) Target link when clicking the logo.

.. _Navigate_ResultsOptions_nav_bar:

-  ``nav_bar`` :index:`: <pair: output - navigate_results - options; nav_bar>` [:ref:`boolean <boolean>`] (default: ``true``) Add a side navigation bar to quickly access to the outputs.

.. _Navigate_ResultsOptions_render_markdown:

-  ``render_markdown`` :index:`: <pair: output - navigate_results - options; render_markdown>` [:ref:`boolean <boolean>`] (default: ``true``) If True, markdown files are rendered; otherwise, they are treated like other files.

.. _Navigate_ResultsOptions_skip_not_run:

-  ``skip_not_run`` :index:`: <pair: output - navigate_results - options; skip_not_run>` [:ref:`boolean <boolean>`] (default: ``false``) Skip outputs with `run_by_default: false`.

.. _Navigate_ResultsOptions_title:

-  ``title`` :index:`: <pair: output - navigate_results - options; title>` [:ref:`string <string>`] (default: ``''``) Title for the page, when empty KiBot will try using the schematic or PCB title.
   If they are empty the name of the project, schematic or PCB file is used. |br|
   You can use %X values and KiCad variables here.

.. _Navigate_ResultsOptions_title_url:

-  ``title_url`` :index:`: <pair: output - navigate_results - options; title_url>` [:ref:`string <string>` | :ref:`boolean <boolean>`] (default: ``''``) Target link when clicking the title, use false to remove.
   KiBot will try with the origin of the current git repo when empty.


