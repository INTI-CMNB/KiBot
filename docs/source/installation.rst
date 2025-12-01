.. index::
   single: installation

Installation
------------

In general the simplest way to start using KiBot is using docker.
This is because you can download docker images containing all the
needed dependencies. Once you are familiarized with KiBot, installing
it locally will offer better performance. Docker can run KiBot for
Windows, macOS and Linux.

When you don't use docker images: KiBot main target is Linux, but some
users successfully use it on Windows. For Windows you’ll need to
install tools to mimic a Linux environment, like WSL2 (part of Windows
10 and newer). Running KiBot on macOS should be possible now
that KiCad migrated to Python 3.x, volunteers to test it are welcome.

You can also run KiBot using docker images in a CI/CD environment like
GitHub or GitLab. In this case you don’t need to install anything
locally.


.. index::
   pair: installation; docker

Installation using docker
~~~~~~~~~~~~~~~~~~~~~~~~~

The basic idea is to:

1. Install docker
2. Download the docker image
3. Run the docker image containing KiBot

There are many ways to achieve this, here is a more detailed description for
Linux:

1. Install docker on your system. You just need the Docker Engine,
   but you can use Docker Desktop (which includes Docker Engine).

   - To install Docker Engine visit this `site <https://docs.docker.com/engine/install/>`__
   - Once docker is installed make sure your user has rights to run
     docker, the docs explains how to run a simple example:

     .. code-block:: bash

        docker run hello-world

     You should be able to run it without the need to use `root` or `sudo`.
     Otherwise you'll need to follow the instructions about what to do after
     installation (i.e. add your user to the *docker* group and reload groups,
     `try here <https://docs.docker.com/engine/install/linux-postinstall/>`__).

2. To download the docker image for KiCad 8 just run:

   .. code-block:: bash

      docker pull ghcr.io/inti-cmnb/kicad8_auto_full:latest

   Replace **8** by the KiCad version you are using (i.e. *kicad7_auto_full*
   for KiCad **7**). This will download all the needed tools.

   - If you need to test the current development code replace *latest*
     by *dev*.
   - If you need to save disk space, and you don't need high quality
     3D renders and PDF reports you can try the smaller images.
     They are named like this: *kicad8_auto* (without *full*)


3. Start the docker image. As a first approach you can try using a
   script like this: (`downloadable <https://github.com/INTI-CMNB/KiBot/blob/dev/tools/docker_kibot_linux.sh>`__)

   .. code-block:: bash

      #!/bin/sh
      export USER_ID=$(id -u)
      export GROUP_ID=$(id -g)
      docker run --rm -it \
          --user $USER_ID:$GROUP_ID \
          --env NO_AT_BRIDGE=1 \
          --env DISPLAY=$DISPLAY \
          --workdir="/home/$USER" \
          --volume=/tmp/.X11-unix:/tmp/.X11-unix \
          --volume="/etc/group:/etc/group:ro" \
          --volume="/etc/passwd:/etc/passwd:ro" \
          --volume="/etc/shadow:/etc/shadow:ro" \
          --volume="/home/$USER:/home/$USER:rw" \
          ghcr.io/inti-cmnb/kicad8_auto_full:latest /bin/bash

   Here you should replace *ghcr.io/inti-cmnb/kicad8_auto_full:latest*
   by the name of the docker image you downloaded. Don't forget to make the
   script executable using, assuming you used the same name used in the repo:

   .. code-block:: bash

      chmod +x docker_kibot_linux.sh

   This script will:

   - Use the system users in your docker image. So you can change users
     like in your system.
   - Start using the same user you are using in your main system.
   - Mount the *home* of your user in the docker image, so you can access
     your files from the docker image.
   - Export your graphics environment information so you can even run
     the KiCad in the docker image and display it in your graphics
     environment.
     Note that you might need to run:

     .. code-block:: bash

        xhost +local:docker

     from a graphics terminal so applications in the docker image can get
     access to your screen.
   - Start with a shell (*/bin/bash*) with your *home* as the current directory
   - Note that when you exit this docker image (just executing *exit*
     from the created shell) the docker instance will be stopped and
     any change to the image itself will be discarded (**--rm**)

   Once running the docker image you can try:

  .. code-block:: bash

     kibot --version

.. index::
   pair: Blender; from docker

.. _docker_script:

A more elaborated script for docker images on Linux
===================================================

The following (`script <https://github.com/INTI-CMNB/KiBot/blob/dev/tools/docker_kibot_linux_allow.sh>`__)
can be used to run KiBot from a docker image with some versatility.

The script takes two optional arguments:

1. The name of the command to run inside the docker container. By default is
   */bin/bash*, so you get a bash shell.
2. The name of the docker image to use. Currently *kicad8_auto_full:latest*,
   but might change in the future.

It will use the current directory, so you can do things like:

.. code-block:: bash

   docker_kibot_linux_allow.sh "kibot --quick-start"

To run KiBot in quick-start mode in the current directory. Note that this
assumes the current directory can be accessed from your user *home*.

You can also check the version of KiBot found in different docker images
like this:

.. code-block:: bash

   docker_kibot_linux_allow.sh "kibot --version" kicad8_auto_full:latest
   docker_kibot_linux_allow.sh "kibot --version" kicad8_auto_full:dev

Or you can even run the KiCad inside the docker image:

.. code-block:: bash

   docker_kibot_linux_allow.sh kicad

Even run an old version of KiCad:

.. code-block:: bash

   docker_kibot_linux_allow.sh kicad kicad7_auto_full:latest

Note that the script gives access to the current user to connect to your
display, this is normally what you want to do.

Be careful with the quotes, the first argument is the command that we pass
to docker. From the point of view of the script, and docker, is just one
string, but can be multiple arguments once inside the docker container
("kibot --version" becomes "kibot" "--version").

Additionaly this script can run Blender from the docker image, just rename
it *blender* and run the script pretending this is blender. In this case
all arguments are passed to Blender and you can't select which docker image
is used.


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
   pair: Blender; Debian
   pair: Blender; Ubuntu

About Blender on Debian systems
===============================

The Debian maintainer disagrees with Intel people about the AI denoiser used by
Blender and distributes a package with it disabled. If you use the official
Debian package you'll need to enable the `no_denoiser` option. This might
seem simple, but the problem is that on CI/CD environments Blender won't use
GPU accelerated render, so the lack of a denoiser means you need 10 times
more time to render the image.

To make things worst the pcb2blender plug-in is very dependant on the Blender
version (Blender fault). The simplest solution is to run Blender from the
docker images, even on a local system. For this you can use the
:ref:`following script <docker_script>`.


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

Also note that in modern Linux system you might need to add the
*--break-system-packages* option.

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
   pair: installation; pipx

Installation using pipx
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: shell

   pipx install kibot --system-site-packages --pip-args="--no-compile"


Note that most of the things explained for `pip` and `virtualenv` might apply
to the use of `pipx`.


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

-  Install KiCad 6.0.11 or newer
-  Install Python 3.7 or newer
-  Install the Python Yaml and requests modules
-  Run the script *src/kibot*


.. index::
   pair: installation; dependencies

Dependencies
~~~~~~~~~~~~

Notes:

- When installing from the `Debian repo <https://set-soft.github.io/debian/>`__, you
  don’t need to worry about dependencies, just pay attention to *recommended* and
  *suggested* packages.
- All dependencies are available in the *full* docker images.
- When installing using ``pip`` the dependencies marked with
  |PyPi dependency| will be automatically installed.
- The dependencies marked with |Auto-download| can be downloaded on-demand
  by KiBot. Note this is poorly tested and is mostly oriented to 64 bits
  Linux systems. Please report problems.
- The ``kibot-check`` tool can help you to know which dependencies are missing.
- Note that on some systems (i.e. Debian) ImageMagick disables PDF
  manipulation in its ``policy.xml`` file. Comment or remove lines like this:
  ``<policy domain="coder" rights="none" pattern="PDF" />`` (On Debian:
  ``/etc/ImageMagick-6/policy.xml``).

  Here is an example for the case of Debian 12:

     .. code-block:: bash

        sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<!-- <policy domain="coder" rights="none" pattern="PDF" \/> -->/g' /etc/ImageMagick-6/policy.xml
        sed -i 's/<policy domain="coder" rights="none" pattern="PS" \/>/<!-- <policy domain="coder" rights="none" pattern="PS" \/> -->/g' /etc/ImageMagick-6/policy.xml

  For more information consult `this post <https://stackoverflow.com/questions/52998331/imagemagick-security-policy-pdf-blocking-conversion>`__

- |Debian| Link to Debian stable package.
- |Python module| This is a Python module, not a separated
  tool.
- |Tool| This is an independent tool, can be a binary or a Python script.

.. include:: dependencies.rst




.. |Debian| image:: https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/debian-openlogo-22x22.png
.. |Python module| image:: https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/Python-logo-notext-22x22.png
.. |Tool| image:: https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/llave-inglesa-22x22.png
