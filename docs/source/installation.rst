.. index::
   single: installation

Installation
------------

KiBot main target is Linux, but some users successfully use it on
Windows. For Windows you’ll need to install tools to mimic a Linux
environment. Running KiBot on MacOSX should be possible now that KiCad
migrated to Python 3.x.

You can also run KiBot using docker images in a CI/CD environment like
GitHub or GitLab. In this case you don’t need to install anything
locally.


.. index::
   pair: installation; dependencies

Dependencies
~~~~~~~~~~~~

Notes:

- When installing from the `Debian repo <https://set-soft.github.io/debian/>`__ you
  don’t need to worry about dependencies, just pay attention to *recommended* and
  *suggested* packages.
- When installing using ``pip`` the dependencies marked with
  |PyPi dependency| will be automatically installed.
- The dependencies marked with |Auto-download| can be downloaded on-demand
  by KiBot. Note this is poorly tested and is mostly oriented to 64 bits
  Linux systems. Please report problems.
- The ``kibot-check`` tool can help you to know which dependencies are missing.
- Note that on some systems (i.e. Debian) ImageMagick disables PDF
  manipulation in its ``policy.xml`` file. Comment or remove lines like this:
  ``<policy domain="coder" rights="none" pattern="PDF" />`` (On Debian:
  ``/etc/ImageMagick-6/policy.xml``)
- |Debian| Link to Debian stable package.
- |Python module| This is a Python module, not a separated
  tool.
- |Tool| This is an independent tool, can be a binary or a Python script.

.. include:: dependencies.rst

.. index::
   pair: installation; Ubuntu
   pair: installation; Debian

Installation on Ubuntu or Debian
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way is to use the
`repo <https://set-soft.github.io/debian/>`__, but if you want to
manually install the individual ``.deb`` files you can:

Get the Debian package from the `releases
section <https://github.com/INTI-CMNB/KiBot/releases>`__ and run:

.. code:: shell

   sudo apt install ./kibot*_all.deb

**Important note**: Sometimes the release needs another packages that
aren’t part of the stable Debian distribution. In this case the packages
are also included in the release page. As an example version 0.6.0
needs:

.. code:: shell

   sudo apt install ./python3-mcpy_2.0.2-1_all.deb ./kibot_0.6.0-1_all.deb

**Important note**: The `KiCad Automation
Scripts <https://github.com/INTI-CMNB/kicad-automation-scripts/>`__
packages are a mandatory dependency. The
`KiBoM <https://github.com/INTI-CMNB/KiBoM>`__,
`InteractiveHtmlBom <https://github.com/INTI-CMNB/InteractiveHtmlBom>`__
and `PcbDraw <https://github.com/INTI-CMNB/PcbDraw>`__ are recommended.


.. index::
   pair: installation; Arch Linux

Installation on Arch Linux
~~~~~~~~~~~~~~~~~~~~~~~~~~

AUR repository for `kibot <https://aur.archlinux.org/packages/kibot>`__

.. code:: shell

   yay -S kibot


.. index::
   pair: installation; pip

Installation using pip
~~~~~~~~~~~~~~~~~~~~~~

.. code:: shell

   pip install --no-compile kibot

Note that ``pip`` has the dubious idea of compiling everything it
downloads. There is no advantage in doing it and it interferes with the
``mcpy`` macros. Also note that in modern Linux systems ``pip`` was
renamed to ``pip3``, to avoid confusion with ``pip`` from Python 2.

If you are installing at system level I recommend generating the
compilation caches after installing. As ``root`` just run:

.. code:: shell

   kibot --help-outputs > /dev/null

Note that ``pip`` will automatically install all the needed Python
dependencies. But it won’t install other interesting dependencies. In
particular you should take a look at the `KiCad Automation
Scripts <https://github.com/INTI-CMNB/kicad-automation-scripts/>`__
dependencies. If you have a Debian based OS I strongly recommend trying
to use the ``.deb`` packages for all the tools.

If you want to install the code only for the current user add the
``--user`` option.

If you want to install the last git code from GitHub using pip use:

.. code:: shell

   pip3 install --user git+https://github.com/INTI-CMNB/KiBot.git

You can also clone the repo, change to its directory and install using:

.. code:: shell

   pip3 install --user -e .

In this way you can change the code and you won’t need to install again.


.. index::
   pair: installation; virtualenv

Notes about virtualenv
~~~~~~~~~~~~~~~~~~~~~~

If you try to use a Python virtual environment you’ll need to find a way
to make the KiCad module (``pcbnew``) available on it. From the `linked
GitHub issue
<https://github.com/yaqwsx/PcbDraw/issues/119#issuecomment-1274029481>`_
, to make the ``pcbnew`` available on the virtual env, you will need to
run the following command:

.. code:: shell

  python -m venv --system-site-packages venv

Then python started in the venv will look at the packages in the system
location, which is where KiCad puts its python code.

In addition: note that the virtual env will change the system share data
paths. They will no longer point to things like ``/usr/share/`` but to a
virtual env place. So you’ll need to either define environment variables
to tell KiBot where are the libs or just add symlinks from the virtual
env to the system level libs.


.. index::
   single: installation; other targets

Installation on other targets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Install KiCad 5.1.6 or newer
-  Install Python 3.5 or newer
-  Install the Python Yaml and requests modules
-  Run the script *src/kibot*


.. |Debian| image:: https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/debian-openlogo-22x22.png
.. |Python module| image:: https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/Python-logo-notext-22x22.png
.. |Tool| image:: https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/llave-inglesa-22x22.png
