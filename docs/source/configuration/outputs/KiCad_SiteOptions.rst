.. _KiCad_SiteOptions:

:orphan:


KiCad_SiteOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **base_url** :index:`: <pair: output - kicad_site - options; base_url>` [:ref:`string <string>`] (default: ``''``) Base URL for the generated site. I.e. https://USER.github.io/PROJECT/
   Without the version part.
-  **title** :index:`: <pair: output - kicad_site - options; title>` [:ref:`string <string>`] (default: ``''``) Title for the site, leave empty to use the one from `hugo.yaml`.
   %X and KiCad variables are expanded.
-  ``assembly_models`` :index:`: <pair: output - kicad_site - options; assembly_models>`  [:ref:`KiCad_SiteAssembly parameters <KiCad_SiteAssembly>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: ``[]``) 3D assembly models.
-  ``bom`` :index:`: <pair: output - kicad_site - options; bom>` [:ref:`string <string>`] (default: ``''``) Name of the BoM output to use as embedded HTML. Use `None` to skip.
-  ``dest_subdir`` :index:`: <pair: output - kicad_site - options; dest_subdir>` [:ref:`string <string>`] (default: ``'static'``) Subdirectory where the files will be copied inside the destination `dir`.
-  ``diffs`` :index:`: <pair: output - kicad_site - options; diffs>`  [:ref:`KiCad_SiteDiff parameters <KiCad_SiteDiff>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: ``[]``) Diff resources, usually one for the PCB and another for the schematic.
-  ``downloads`` :index:`: <pair: output - kicad_site - options; downloads>`  [:ref:`KiCad_SiteDownload parameters <KiCad_SiteDownload>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: ``[]``) Downloadable resources for releases, not for `latest`.
-  ``force_copy`` :index:`: <pair: output - kicad_site - options; force_copy>` [:ref:`boolean <boolean>`] (default: ``false``) By default we skip the copy to the destination dir if the file is already there and newer.
   Enabling this option we always do the copy.
-  ``ibom`` :index:`: <pair: output - kicad_site - options; ibom>` [:ref:`string <string>`] (default: ``''``) Name of the iBoM output. Use `None` to skip.
-  ``kiri`` :index:`: <pair: output - kicad_site - options; kiri>` [:ref:`string <string>`] (default: ``''``) Name of the KiRi output to use as embedded HTML. Use `None` to skip.
-  ``pcb_first`` :index:`: <pair: output - kicad_site - options; pcb_first>` [:ref:`boolean <boolean>`] (default: ``false``) List the PCB first, KiCanvas will show the PCB by default, instead of the schematic.
-  ``renders`` :index:`: <pair: output - kicad_site - options; renders>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``''``) Name of one or more outputs providing images for the PCB.

-  ``version`` :index:`: <pair: output - kicad_site - options; version>` [:ref:`string <string>`] (default: ``'auto'``) Version for the generated site. `auto` tries to figure out it.
   Currently it just uses the GITHUB_REF environment variable to detect a tag, otherwise it
   just assumes this is `latest`.

Used dicts
----------

- :ref:`KiCad_SiteAssembly parameters <KiCad_SiteAssembly>`
- :ref:`KiCad_SiteDiff parameters <KiCad_SiteDiff>`
- :ref:`KiCad_SiteDownload parameters <KiCad_SiteDownload>`
