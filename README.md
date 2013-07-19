kicad-utils
===========

This repository contains a collection of scripts and cool stuff for KiCad.

I use KiCad to design my boards, and I submit them to SeeedStudio. The content of this place is mostly related to this manufacturer.

panelize.py
-----------
This script is an adaptation from http://blog.borg.ch/?p=12 to fit my needs. Main modification so far is the use of metric system.

mergedrl
--------
This script is a clone from https://github.com/9dof/kicad-utils
SeeedStudio requires a single drill file (.txt) and KiCad produces (at least) two: one for plated thru holes and one for non-plated thru holes (named NPTH).
This Perl script makes the job of merging both files in a single one.

svg2silk
--------
This script is an original work which allows to draw SVG image onto PCB silkscreen.
