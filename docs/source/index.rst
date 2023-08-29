KiBot (formerly KiPlot)
=======================

.. figure:: https://raw.githubusercontent.com/INTI-CMNB/KiBot/master/docs/images/kibot_740x400_logo.png
   :alt: KiBot Logo

|Python application| |Coverage Status| |PyPI version| |Donate|

|doc_id|

**Important for CI/CD**:

- The GitHub actions now use the full/test docker images. So now they include PanDoc and also Blender.
- If you are looking for the GitHub Actions documentation, and you already know how
  to use KiBot, or want a quick start, read: :ref:`usage-of-github-actions`

**New on v1.6.3**

- Parametrizable imports
- ``value_split`` and ``spec_to_field`` filters


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   introduction
   installation
   configuration
   usage
   usage_with_ci_cd

.. toctree::
   :maxdepth: 3
   :caption: Notes and extra information:

   notes_gerber
   notes_position
   notes_3d
   propose
   KiPlotYAML

.. toctree::
   :maxdepth: 2
   :caption: Final notes:

   contributing
   credits

.. toctree::
   :maxdepth: 2
   :caption: Indices and tables:

   genindex


.. |Coverage Status| image:: https://img.shields.io/coveralls/github/INTI-CMNB/KiBot?style=plastic
   :target: https://coveralls.io/github/INTI-CMNB/KiBot?branch=master
.. |PyPI version| image:: https://img.shields.io/pypi/v/kibot?style=plastic
   :target: https://pypi.org/project/kibot/
.. |Donate| image:: https://img.shields.io/badge/Donate-PayPal-green.svg?style=plastic
   :target: https://www.paypal.com/donate/?hosted_button_id=K2T86GDTTMRPL