.. Automatically generated by KiBot, please don't edit this file

.. index::
   pair: Draw Stackup; draw_stackup

Draw Stackup
~~~~~~~~~~~~

Draw the PCB stackup. Needs KiCad 7 or newer.
To specify the position and size of the drawing you can use two methods. |br|
You can specify it using the *pos_x*, *pos_y*, *width*, *height* and *layer* options. |br|
But you can also create a group called *kibot_stackup*. If you don't know how to
create a group consult :ref:`create_group`. After running this preflight the rectangle
will contain the stackup

   -  **draw_stackup** :index:`: <pair: preflight - draw_stackup; draw_stackup>`  [:ref:`DrawStackupOptions parameters <DrawStackupOptions_pre>`] [:ref:`boolean <boolean>` | :ref:`dict <dict>`] (default: ``false``) Use a boolean for simple cases or fine-tune its behavior.

.. toctree::
   :caption: Used dicts

   DrawStackupOptions
