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

#from kicad import *
import kicad
import svg
import sys
import copy

def draw(f, m):
    for draw in f.flatten():
        if isinstance(draw, svg.Circle):
            m.draw(kicad.Circle(draw.center.coord(), draw.radius, 0.1524))
        elif hasattr(draw, 'segments'):
            if draw.style and 'fill' in draw.style and '000000' in draw.style:
                for segment in draw.segments(0.1):
                    m.draw(kicad.Polygon([x.coord() for x in segment]))
                print('style: ' + draw.style)
            else:
                for segment in draw.segments(0.1):
                    pts = [x.coord() for x in segment]
                    pts.reverse()
                    p1 = pts.pop()
                    while pts:
                        p2 = pts.pop()
                        m.draw(kicad.Segment(p1, p2, 0.1524))
                        p1 = p2
        else:
            print("Unsupported SVG element" + draw)

#for s in f.scale(ratio).translate(offset).simplify(0.01):
#    m.draw(kicad.Polygon([x.coord() for x in s]))


fsvg = svg.Svg(sys.argv[1])
name = fsvg.title()
print('Scale ' + name + ' to ' + str(sys.argv[2:]) + ' widths')


l = kicad.LibModule(name + '.mod')

for width in sys.argv[2:]:
    f = copy.deepcopy(fsvg)
    m = kicad.Module(name + '-' + width)
    m.reference('G*')
    m.value(name)

    # Scale to 'width'
    a,b = f.bbox()
    ratio = int(width)/(b-a).x
    # Centering offset
    offset = (a-b)*0.5*ratio
    f.scale(ratio)
    draw(f,m)
    l.add_module(m)

l.write()

