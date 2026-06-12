.. index::
   pair: notes; 3D models

Notes about 3D models
---------------------

This section contains some notes and advices about the use of 3D models.
There are many strategies and you can choose the mix that better suits
your needs. If you have any suggestion don’t hesitate in contacting me
to add them.


.. index::
   pair: 3D models; docker

3D models and docker images
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default KiCad 3D models aren’t included in the KiBot docker images.
This is because the 3D models currently needs around 5 GB and the
current docker images are between 1 and 2.8 GB. So adding them means a
huge increase in size.

This is not a big problem because KiBot will download any missing 3D
model from KiCad’s repo.

As a side effect you’ll get errors and/or warnings about the missing 3D
models and/or KiCad environment variables pointing to them.

If you need to install the KiCad 3D models in one of the
``kicad_debian``, ``kicad_auto`` or ``kicad_auto_test`` images just run
the ``/usr/bin/kicad_3d_install.sh`` script included with the current
images.

If you are running the GitHub action and you want to install the KiCad
3D models use the ``install3D: YES`` option.


.. index::
   pair: 3D models; cache

Caching downloaded 3D models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can store the downloaded 3D models in a GitHub cache, an example can
be found in the following
`repo <https://github.com/set-soft/kibot_3d_models_cache_example>`__


.. index::
   pair: 3D models; recommendations

Self contained projects
~~~~~~~~~~~~~~~~~~~~~~~

Try to make your project self contained. If you are using a repo this
means the repo should contain anything needed to work with your project.

KiCad 6 helps a lot in this regard. Now schematic files are self
contained, you don’t need external files to work with them. Even with
this I think including the used symbols and footprints isn’t a bad idea.
If you expect other people to edit your project then is much simpler if
the originals are in the project.

The 3D models are a very special case. KiCad doesn’t help much in this
regard. I strongly suggest including all used 3D models in your repo.
You can then use ``${KIPRJMOD}`` as base for the path to the models,
this will be expanded to the current path to your project. So you can
use things like ``${KIPRJMOD}/3D/MODEL_NAME`` and store all the 3D
models in the *3D* folder inside your project folder.


.. index::
   pair: 3D models; LCSC/JLCPCB/EasyEDA

LCSC/JLCPCB/EasyEDA 3D models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

KiBot can download 3D models for components that has an LCSC code and
that has a 3D model at `EasyEDA <https://easyeda.com/>`__. If the 3D
model is used locally, but not found in the repo, KiBot will try to
download it. Use the ``field_lcsc_part`` global option if KiBot fails
to detect the schematic field containing the LCSC code. To disable the
download mechanism use the ``download_lcsc`` option of the particular
output.


.. index::
   pair: 3D models; aliases

3D models aliases
~~~~~~~~~~~~~~~~~

This is a KiCad 6 feature that was removed in KiCad 7. If you use it
please migrate to environment variables as KiCad 7 did. If you still
interested on it continue reading.

This is a very limited feature in KiCad. You can define an ``ALIAS`` and
then use ``ALIAS:MODEL_NAME``. The ``ALIAS`` will say where to look for
``MODEL_NAME``. This looks coherent with the way KiCad handles symbols
and footprints. But it currently has a huge limitation: this information
is stored along with the user configuration and there is no way to
complement it at project level. I don’t recommend using aliases because
it makes quite complicated to create self contained projects.

KiBot offers some mechanisms to help using aliases:

1. You can define your aliases in the ``global`` section using the
   ``aliases_for_3d_models`` option.
2. You can use environment and text variables to define aliases. This
   can be disabled using the ``disable_3d_alias_as_env`` option.

The problem with this is that you must keep two lists synchronized, one
for KiCad and the other to make your project self contained.


.. index::
   pair: 3D models; PCM
   pair: 3D models; addons

How to handle addons
~~~~~~~~~~~~~~~~~~~~

KiCad 6 introduces a *Plugin and Content Manager*, they can contain
footprints and 3D models. Using 3D models aliases looks like a good
solution here, but this isn’t. The best solution here is to use the
``KICAD6_3RD_PARTY`` variable. Instead of defining an alias pointing to
the content you can just use
``${KICAD6_3RD_PARTY}/3dmodels/FULL_PLUGIN_NAME/MODEL_NAME``. I know
this is long, but this will make your project portable. The user will
need to download the plugin, but won’t need to define any alias.


.. index::
   pair: 3D models; self contained

Getting a self contained PCB
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to help users to create self contained projects KiBot offers
some help. The following configuration:

.. code:: yaml

   # Example KiBot config file
   kibot:
     version: 1

   outputs:
     - name: export_pcb
       comment: 'Copy 3D models'
       type: copy_files
       dir: 'exported_pcb'
       options:
         files:
           - source_type: 3d_models
             dest: 3d_models+
             save_pcb: true

Will create a new PCB inside a directory called ``exported_pcb``, this
PCB will use the 3D models copied to ``exported_pcb/3d_models`` using
relative paths. So you can move the new PCB file to any place, as long
as the ``3d_models`` directory is in the same place as the PCB.
