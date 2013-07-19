# SVG to KiCad silkscreen drawing

# Copyright (C) 2013 -- CJlano < cjlano @ free.fr >

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import kicad
import svg
import sys

f = svg.Svg(sys.argv[1])

l = kicad.LibModule("/tmp/1.mod")
m = kicad.Module("MyTest")
m.reference('G*')
m.value(f.title())

a,b = f.bbox()
# We want a 10.0mm width logo
width = 100.0
ratio = width/(b-a).x
# Centering offset
offset = (a-b)*0.5*ratio

for draw in f.drawing:
    if isinstance(draw, svg.Path):
        for segment in draw.simplify(0.1):
            pts = [x.coord() for x in segment]
            pts.reverse()
            p1 = pts.pop()
            while pts:
                p2 = pts.pop()
                m.draw(kicad.Segment(p1, p2, 0.20))
                p1 = p2
    elif isinstance(draw, svg.Circle):
        m.draw(kicad.Circle(draw.center.coord(), draw.radius, 0.20))
    else:
        print("Unsupported SVG element" + draw)

#for s in f.scale(ratio).translate(offset).simplify(0.01):
#    m.draw(kicad.Polygon([x.coord() for x in s]))

l.add_module(m)
l.write()

