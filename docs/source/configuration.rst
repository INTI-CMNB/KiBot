.. index::
   single: configuration

.. _configuration:

Configuration
-------------

KiBot uses a configuration file where you can specify what *outputs* to
generate and which preflight (before *launching* the outputs generation)
actions to perform. By default you’ll generate all of them, but you can
specify which ones from the command line.

The configuration file should be named using the **.kibot.yaml** suffix,
i.e. *my_project.kibot.yaml*. The format used is
`YAML <https://yaml.org/>`__. This is basically a text file with some
structure. This file can be compressed using *gzip* file format.

If you never used YAML read the following :ref:`explanation <kiplot-yaml>`.
Note that the explanation could be useful even if you know YAML.

Helper for writing the configuration
------------------------------------

Some text editors supports YAML schemas to validate and help writing YAML
files. For KiBot you can use the following schema:

*https://cdn.jsdelivr.net/gh/INTI-CMNB/KiBot@master/docs/kibot_schema.json*

When using a development version of KiBot use the following schema:

*https://cdn.jsdelivr.net/gh/INTI-CMNB/KiBot@dev/docs/kibot_schema.json*


Configuration for VSCode/VSCodium
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This instructions are for the `YAML` extension from *Red Hat*. This will
provide autocompletion, tool tip helpers and option validation.

In your `settings.json` add an entry for the KiBot schema, like this:

.. code-block:: json

   "yaml.schemas": {
      "https://cdn.jsdelivr.net/gh/INTI-CMNB/KiBot@master/docs/kibot_schema.json": ["*.kibot.yaml", "*kibot*.yaml"]
   }

This will use the KiBot schema for any file matching the above patterns.
If you prefer to add it to the KiBot files use:

.. code-block:: yaml

   # yaml-language-server: $schema=https://cdn.jsdelivr.net/gh/INTI-CMNB/KiBot@master/docs/kibot_schema.json

   kibot:
     version: 1

Replace `master` by `dev` if you are using KiBot from the development branch.


.. toctree::
   :maxdepth: 3
   :caption: Configuration:

   configuration/quick_start
   configuration/section_order
   configuration/header
   configuration/outputs
   configuration/preflight
   configuration/global
   configuration/filters
   configuration/imports
   configuration/substitution
