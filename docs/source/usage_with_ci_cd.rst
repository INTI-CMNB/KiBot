.. index::
   pair: usage; CI/CD

.. _usage-of-github-actions:

Usage for CI/CD
---------------

When using a GitHub or GitLab repo you can use KiBot to generate all the
needed stuff each time you commit a change to the schematic and/or PCB
file.

If you want a quick demo of what KiBot can do on a GitHub project try
the following
`workflow <https://github.com/INTI-CMNB/kibot_variants_arduprog/blob/master/.github/workflows/kibot_quick_start.yml>`__.
You just need to enable GitHub workflows and copy this workflow to your
``.github/workflows/`` folder. In this mode KiBot will detect the
project files, create a configuration and generate the targets. This
workflow collects the generated files in ``Automatic_outputs.zip``.

Examples of how to use KiBot can be found `here for
GitHub <https://github.com/INTI-CMNB/kicad_ci_test>`__ and `here for
GitLab <https://gitlab.com/set-soft/kicad-ci-test>`__.

In order to run KiBot on these environments you need a lot of software
installed. The usual mechanism to achieve this is using
`docker <https://www.docker.com/>`__. Docker images containing KiBot,
all the supporting scripts and a corresponding KiCad can be found in the
`kicad5_auto <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad5_auto>`__,
`kicad6_auto <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad6_auto>`__,
`kicad7_auto <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad7_auto>`__
and
`kicad8_auto <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad8_auto>`__
GitHub packages. More complete images, with Pandoc, LaTeX, Blender and
testing tools, can be found in the following packages:
`kicad5_auto_full <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad5_auto_full>`__,
`kicad6_auto_full <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad6_auto_full>`__,
`kicad7_auto_full <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad7_auto_full>`__
and
`kicad8_auto_full <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad8_auto_full>`__
GitHub packages. Old images can be found at `Docker
Hub <https://hub.docker.com/>`__ as
`setsoft/kicad_auto <https://hub.docker.com/repository/docker/setsoft/kicad_auto>`__
and
`setsoft/kicad_auto_test <https://hub.docker.com/repository/docker/setsoft/kicad_auto_test>`__.

The images are based on
`kicad5_debian <https://github.com/INTI-CMNB/kicad_debian/pkgs/container/kicad5_debian>`__,
`kicad6_debian <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad6_debian>`__,
`kicad7_debian <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad7_debian>`__
and
`kicad8_debian <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad8_debian>`__.
(`setsoft/kicad_debian <https://hub.docker.com/repository/docker/setsoft/kicad_debian>`__
on Docker Hub), containing KiCad on Debian GNU/Linux.

If you need to run the current development version of KiBot you can use
the following docker images:
`ghcr.io/inti-cmnb/kicad5_auto_full:dev <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad5_auto_full>`__,
`ghcr.io/inti-cmnb/kicad6_auto_full:dev <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad6_auto_full>`__,
`ghcr.io/inti-cmnb/kicad7_auto_full:dev <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad7_auto_full>`__
or
`ghcr.io/inti-cmnb/kicad8_auto_full:dev <https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad8_auto_full>`__
(`setsoft/kicad_auto:dev <https://hub.docker.com/repository/docker/setsoft/kicad_auto>`__).
These images are based on the *full* (also named *test*) images.

The most important images are:

.. index::
   pair: docker; tags
   pair: CI/CD; tags

========================================= ============ =======
Name                                      KiBot        KiCad
========================================= ============ =======
ghcr.io/inti-cmnb/kicad5_auto_full:latest last release 5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:latest last release 6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:latest last release 7.0.11
ghcr.io/inti-cmnb/kicad8_auto_full:latest last release 8.0.8
ghcr.io/inti-cmnb/kicad9_auto_full:latest last release 9.x
ghcr.io/inti-cmnb/kicad5_auto:latest      last release 5.1.9
ghcr.io/inti-cmnb/kicad6_auto:latest      last release 6.0.11
ghcr.io/inti-cmnb/kicad7_auto:latest      last release 7.0.11
ghcr.io/inti-cmnb/kicad8_auto:latest      last release 8.0.8
ghcr.io/inti-cmnb/kicad9_auto:latest      last release 9.x
ghcr.io/inti-cmnb/kicad5_auto_full:dev    git code     5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:dev    git code     6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:dev    git code     7.0.11
ghcr.io/inti-cmnb/kicad8_auto_full:dev    git code     8.0.8
ghcr.io/inti-cmnb/kicad9_auto_full:dev    git code     9.x
ghcr.io/inti-cmnb/kicad6_auto_full:1.8.4  1.8.4        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.8.4  1.8.4        7.0.11
ghcr.io/inti-cmnb/kicad8_auto_full:1.8.4  1.8.4        8.0.8
ghcr.io/inti-cmnb/kicad9_auto_full:1.8.4  1.8.4        9.0.1
ghcr.io/inti-cmnb/kicad5_auto_full:1.8.3  1.8.3        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.8.3  1.8.3        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.8.3  1.8.3        7.0.11
ghcr.io/inti-cmnb/kicad8_auto_full:1.8.3  1.8.3        8.0.8
ghcr.io/inti-cmnb/kicad9_auto_full:1.8.3  1.8.3        9.0.0
ghcr.io/inti-cmnb/kicad5_auto_full:1.8.2  1.8.2        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.8.2  1.8.2        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.8.2  1.8.2        7.0.11
ghcr.io/inti-cmnb/kicad8_auto_full:1.8.2  1.8.2        8.0.8
ghcr.io/inti-cmnb/kicad5_auto_full:1.8.1  1.8.1        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.8.1  1.8.1        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.8.1  1.8.1        7.0.11
ghcr.io/inti-cmnb/kicad8_auto_full:1.8.1  1.8.1        8.0.5
ghcr.io/inti-cmnb/kicad5_auto_full:1.7.0  1.7.0        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.7.0  1.7.0        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.7.0  1.7.0        7.0.11
ghcr.io/inti-cmnb/kicad8_auto_full:1.7.0  1.7.0        8.0.4
ghcr.io/inti-cmnb/kicad5_auto_full:1.6.5  1.6.5        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.6.5  1.6.5        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.6.5  1.6.5        7.0.11
ghcr.io/inti-cmnb/kicad8_auto_full:1.6.5  1.6.5        8.0.1
ghcr.io/inti-cmnb/kicad5_auto_full:1.6.4  1.6.4        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.6.4  1.6.4        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.6.4  1.6.4        7.0.11
ghcr.io/inti-cmnb/kicad5_auto_full:1.6.3  1.6.3        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.6.3  1.6.3        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.6.3  1.6.3        7.0.10
ghcr.io/inti-cmnb/kicad5_auto_full:1.6.2  1.6.2        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.6.2  1.6.2        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.6.2  1.6.2        7.0.5.1
ghcr.io/inti-cmnb/kicad5_auto_full:1.6.1  1.6.1        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.6.1  1.6.1        6.0.11
ghcr.io/inti-cmnb/kicad7_auto_full:1.6.1  1.6.1        7.0.2.1
ghcr.io/inti-cmnb/kicad5_auto_full:1.6.0  1.6.0        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.6.0  1.6.0        6.0.10
ghcr.io/inti-cmnb/kicad5_auto_full:1.5.1  1.5.1        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.5.1  1.5.1        6.0.10
ghcr.io/inti-cmnb/kicad5_auto_full:1.4.0  1.4.0        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.4.0  1.4.0        6.0.9
ghcr.io/inti-cmnb/kicad5_auto_full:1.3.0  1.3.0        5.1.9
ghcr.io/inti-cmnb/kicad6_auto_full:1.3.0  1.3.0        6.0.7
ghcr.io/inti-cmnb/kicad5_auto:1.2.0       1.2.0        5.1.9
ghcr.io/inti-cmnb/kicad6_auto:1.2.0       1.2.0        6.0.5
========================================= ============ =======

For more information about the docker images visit
`kicad_debian <https://github.com/INTI-CMNB/kicad_debian>`__ and
`kicad_auto <https://github.com/INTI-CMNB/kicad_auto>`__.

.. index::
   pair: usage; GitHub

GitHub workflows
~~~~~~~~~~~~~~~~

A work-in-progress guide can be found `here <https://github.com/INTI-CMNB/KiBot/blob/dev/docs/GITHUB-ACTIONS-README.md>`__.


.. index::
   pair: usage; GitHub Actions

Usage of GitHub Actions
~~~~~~~~~~~~~~~~~~~~~~~

Note: You can also use –quick-start functionality with GitHub actions,
an example is this
`workflow <https://github.com/INTI-CMNB/kibot_variants_arduprog/blob/master/.github/workflows/kibot_action_quick_start.yml>`__.
This is the fastest way to test KiBot functionality.

You need to put a :ref:`config.kibot.yaml <configuration>` file into the
KiCad project folder.

Here is an example of workflow file using the GitHub Action:

.. code:: yaml

   name: example

   on:
     push:
       paths:
       - '**.sch'
       - '**.kicad_pcb'
     pull_request:
       paths:
         - '**.sch'
         - '**.kicad_pcb'

   jobs:
     example:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v2
       - uses: INTI-CMNB/KiBot@v2_k8
         with:
           # Required - kibot config file
           config: config.kibot.yaml
           # optional - prefix to output defined in config
           dir: output
           # optional - schematic file
           schema: 'schematic.sch'
           # optional - PCB design file
           board: 'pcb.kicad_pcb'
       - name: upload results
         if: ${{ always() }}
         uses: actions/upload-artifact@v4
         with:
           name: output
           path: output

For KiCad 5 use ``v2`` instead of ``v2_k8`` (``v2_k7`` for KiCad 7
or ``v2_k6`` for KiCad 6).
These actions use the last KiBot stable release, to use the current
development code use ``v2_dk8`` (KiCad 8) (``v2_dk7``, ``v2_dk6``, ``v2_d``).

Note: the `if: ${{ always() }}` is used to collect artifacts even on fails.

A working example applied to a repo can be found
`here <https://github.com/INTI-CMNB/kicad-ci-test-spora/tree/test_gh_action>`__
(`spora_main.yml <https://github.com/INTI-CMNB/kicad-ci-test-spora/blob/test_gh_action/.github/workflows/spora_main.yml>`__).
Another example, but using variants can be found
`here <https://github.com/INTI-CMNB/kibot_variants_arduprog>`__
(`kibot_action.yml <https://github.com/INTI-CMNB/kibot_variants_arduprog/blob/master/.github/workflows/kibot_action.yml>`__
for KiCad 7,
`kibot_action.yml <https://github.com/INTI-CMNB/kibot_variants_arduprog/blob/KiCad5/.github/workflows/kibot_action.yml>`__
for KiCad 5)

The available options are:

-  **additional_args**: Additional text to add to the KiBot invocation.
   This is intended for advanced use, report problems.
-  **cache3D**: When ``YES`` you can cache the downloaded 3D models. An
   example can be found
   `here <https://github.com/set-soft/kibot_3d_models_cache_example/>`__.
-  **config**: The KiBot config file to use. The first file that matches
   ``*.kibot.yaml`` is used when omitted.
-  **dir**: Output directory for the generated files. The current
   directory is used when omitted.
-  **board**: Name of the PCB file. The first file that matches
   ``*.kicad_pcb`` is used when omitted.
-  **install3D**: When ``YES`` installs the KiCad 3D models. Note that
   this will download more than 360 MiB and install more than 5 GiB of
   files.
-  **quickstart**: When ``YES`` ignores all the other options and runs
   in ``--quick-start`` mode. No configuration needed.
-  **schema**: Name of the schematic file. The first file that matches
   ``*.*sch`` is used when omitted.
-  **skip**: Skip preflights, comma separated or *all*. Nothing is
   skipped when omitted.
-  **targets**: List of targets to generate separated by spaces. To only
   run preflights use **NONE**. All targets are generated when omitted.
-  **variant**: Global variant to use. No variant is applied when
   omitted.
-  **verbose**: Level of verbosity. Valid values are 0, 1, 2 or 3.
   Default is 0.


.. index::
   pair: GitHub Actions; tags

GitHub Actions tags
^^^^^^^^^^^^^^^^^^^

There are several tags you can choose:

=========== === ============ =======
Tag         API KiBot        KiCad
=========== === ============ =======
v1          1   1.2.0        5.1.9
v1_k6       1   1.2.0        6.0.5
v2_1_2_0    2   1.2.0        5.1.9
v2_k6_1_2_0 2   1.2.0        6.0.5
v2_1_3_0    2   1.3.0        5.1.9
v2_k6_1_3_0 2   1.3.0        6.0.7
v2_1_4_0    2   1.4.0        5.1.9
v2_k6_1_4_0 2   1.4.0        6.0.9
v2_1_5_1    2   1.5.1        5.1.9
v2_k6_1_5_1 2   1.5.1        6.0.9
v2_1_6_0    2   1.6.0        5.1.9
v2_k6_1_6_0 2   1.6.0        6.0.9
v2_1_6_2    2   1.6.2        5.1.9
v2_k6_1_6_2 2   1.6.2        6.0.11
v2_k7_1_6_2 2   1.6.2        7.0.5.1
v2_1_6_3    2   1.6.3        5.1.9
v2_k6_1_6_3 2   1.6.3        6.0.11
v2_k7_1_6_3 2   1.6.3        7.0.10
v2_1_6_4    2   1.6.4        5.1.9
v2_k6_1_6_4 2   1.6.4        6.0.11
v2_k7_1_6_4 2   1.6.4        7.0.11
v2_1_6_5    2   1.6.5        5.1.9
v2_k6_1_6_5 2   1.6.5        6.0.11
v2_k7_1_6_5 2   1.6.5        7.0.11
v2_k8_1_6_5 2   1.6.5        8.0.1
v2_1_7_0    2   1.7.0        5.1.9
v2_k6_1_7_0 2   1.7.0        6.0.11
v2_k7_1_7_0 2   1.7.0        7.0.11
v2_k8_1_7_0 2   1.7.0        8.0.4
v2_1_8_1    2   1.8.1        5.1.9
v2_k6_1_8_1 2   1.8.1        6.0.11
v2_k7_1_8_1 2   1.8.1        7.0.11
v2_k8_1_8_1 2   1.8.1        8.0.5
v2_1_8_2    2   1.8.2        5.1.9
v2_k6_1_8_2 2   1.8.2        6.0.11
v2_k7_1_8_2 2   1.8.2        7.0.11
v2_k8_1_8_2 2   1.8.2        8.0.8
v2_1_8_3    2   1.8.3        5.1.9
v2_k6_1_8_3 2   1.8.3        6.0.11
v2_k7_1_8_3 2   1.8.3        7.0.11
v2_k8_1_8_3 2   1.8.3        8.0.8
v2_k9_1_8_3 2   1.8.3        9.0.0
v2_k6_1_8_4 2   1.8.4        6.0.11
v2_k7_1_8_4 2   1.8.4        7.0.11
v2_k8_1_8_4 2   1.8.4        8.0.8
v2_k9_1_8_4 2   1.8.4        9.0.1
v2          2   last release 5.1.9
v2_k6       2   last release 6.0.11
v2_k7       2   last release 7.0.11
v2_k8       2   last release 8.0.8
v2_k9       2   last release 9.x
v2_d        2   git code     5.1.9
v2_dk6      2   git code     6.0.11
v2_dk7      2   git code     7.0.11
v2_dk8      2   git code     8.0.8
v2_dk9      2   git code     9.x
=========== === ============ =======

The main differences between API 1 and 2 are:

-  API 2 adds support for variants and quick-start
-  In API 2 you can select which targets are created
-  In API 1 you must specify the input files, in API 2 can be omitted
-  API 1 supports wildcards in the filenames, API 2 doesn’t
-  API 2 supports spaces in the filenames, API 1 doesn’t

Also note that v2 images are currently using the *full* docker image
(v1.5 and newer). It includes things like PanDoc and Blender.


.. index::
   pair: GitHub; cache

GitHub Cache
~~~~~~~~~~~~

GitHub offers a mechanism to cache data between runs. One interesting
use is to make the KiCost prices cache persistent, here is an
`example <https://github.com/set-soft/kicost_ci_test>`__

Another use is to cache `downloaded 3D
models <https://github.com/set-soft/kibot_3d_models_cache_example>`__

