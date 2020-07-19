.. figure:: http://i.imgur.com/y5Zv9Az.png
   :alt: Revealing the correct card

Installation
------------

``pip install dixit``

Starting the Server
-------------------

``dixit``

Then go to http://localhost:8888/.

Configuring the Server
----------------------

Configuration options, such as the port (default 8888), and the location of
each card deck (e.g., see ``dixit/static/cards/dixit/README.txt``), are housed
in JSON configuration files that are read when you launch the server.
Default settings are located in ``dixit/config.json``.

To override the defaults, you may create a JSON file in your working directory
that contains a subset of these configuration options. For example, to change
the port to 9000, create a new file named ``config.local.json`` that contains:

.. code-block:: JSON

   {
       "port": 9000
   }

Then pass in this file name when you launch the server, as in:
``dixit config.local.json``. This will override the default configuration with
the values in ``config.local.json``.

Alternatively, directly edit ``dixit/config.json``, to for instance, specify
which port to use, or to point to the location of each card deck that you have.

Disclaimer
----------

This software is solely the work of several fans of the Dixit board
game. It is not intended to substitute nor compete with the original
board game, Dixit (a registered trademark of Libellud Company), and
likewise does not represent the works, views, nor opinions of Libellud.
This software is provided as is, without warranty of any kind, express
or implied.

Please support the creators, designers, and artists of Dixit by
purchasing the original board game and its expansions.

We do not currently, nor do we plan to, distribute copywritten artwork.
Currently all cards must be supplied by you, the user. This server is
provided for personal use only (there is no license for commercial use).

Please contact the maintainer if there are any concerns.

Notes
-----

This is an alpha release and may therefore undergo significant changes.
Please request features or submit changes to
https://github.com/arvoelke/Dixit/.

Thank you to all the developers who have helped so far!
