SVG2Silkscreen
==============

This is a Python script which transform SVG image to KiCad module silkscreen drawing.

It uses my [SVG Python](https://github.com/cjlano/svg) and [KiCad Python](https://github.com/cjlano/pykicad) librairies.

Those librairies are referenced here as git submodule. To retrieve them, you need to run the following commands, in the kicad-utils folder (toplevel of the working tree).

    $ git submodule init
    $ git submodule update
This is necessary only once after `git clone` or archive download. Later, use `git submodule update` to update the submodules when needed.

Enjoy!

License: GPLv2+
