.. index::
   single: quick start

Quick start
~~~~~~~~~~~

If you want to *learn by examples*, or you just want to take a look at
what KiBot can do, you can use the ``--quick-start`` command line
option.

First change to the directory where your project (or projects) is
located. Now run KiBot like this:

.. code:: shell

   kibot --quick-start

This will look for KiCad projects starting from the current directory
and going down the directory structure. For each project found KiBot
will generate a configuration file showing some common outputs. After
creating the configuration files KiBot will start the outputs
generation.

Here is an
`example <https://inti-cmnb.github.io/kibot_variants_arduprog_site/Browse/t1-navigate.html>`__
of what’s generated using the following `example
repo <https://inti-cmnb.github.io/kibot_variants_arduprog/>`__.

You can use the generated files as example of how to configure KiBot. If
you want to just generate the configuration files and not the outputs
use:

.. code:: shell

   kibot --quick-start --dry

If you want to know about all the possible options for all the available
outputs you can try:

.. code:: shell

   kibot --example

This will generate a configuration file with all the available outputs
and all their options.
