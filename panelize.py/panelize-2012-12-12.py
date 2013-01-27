#!/usr/bin/env python

# X: 0.9800
# Y: 0.6550

import re
import sys

class Coord:

	def __init__( self, x, y, string=None, delim=None ):
		if string:
			if delim == None:
				raise Exception, "missing delimiter for coord"
			parts = string.split( delim )
			if len( parts ) < 2:
				m = "invalid coord '%s', missing delimiter '%s'" % (
						string, delim )
				raise Exception, m
			if len( parts ) > 2:
				m = "invalid coord '%s', too many parts" % string
				raise Exception, m
			if not parts[0].isdigit() or not parts[1].isdigit():
				m = "invalid coord '%s', parts must be numeric" % string
				raise Exception, m
			x = int(parts[0])
			y = int(parts[1])
		if x == None or y == None:
			raise Exception, "missing parameter for coord"
		self.x = x
		self.y = y

	def to_str( self ):
		return "%d %d" % ( self.x, self.y )

	def __add__( self, c ):
		return Coord( self.x+c.x, self.y+c.y )

	def __sub__( self, c ):
		return Coord( self.x-c.x, self.y-c.y )

	def rot( self, angle ):
		if angle == 0:
			return self
		elif angle == 90:
			return Coord( self.y, -self.x )
		elif angle == 180:
			return Coord( -self.x, -self.y )
		elif angle == 270:
			return Coord( -self.y, self.x )

class Area:

	def __init__( self, p1, p2 ):
		self.tl = p1
		self.br = p2
		if self.tl.x > self.br.x:
			x = self.tl.x
			self.tl.x = self.br.x
			self.br.x = x
		if self.tl.y > self.br.y:
			y = self.tl.y
			self.tl.y = self.br.y
			self.br.y = y

	def inside( self, c ):
		return c.x >= self.tl.x and c.x <= self.br.x and \
				c.y >= self.tl.y and c.y <= self.br.y 

	def get( self, which ):
		if which == "top-left":
			return self.tl
		elif which == "top-right":
			return Coord( self.br.x, self.tl.y )
		elif which == "bottom-left":
			return Coord( self.tl.x, self.br.y )
		elif which == "bottom-right":
			return self.br


class NullTransform:

	def __init__( self ):
		pass

	def coord( self, c ):
		return c

	def rot( self, angle ):
		return angle

	def name( self, name ):
		return name

	def net( self, nr, name ):
		return nr, name


nulltransform = NullTransform()


class RotateTransform:

	def __init__( self, area, cornername, destination, angle, suffix, board ):
		self.area = area
		#self.x1, self.y1 = area.top_left()
		#self.x2, self.y2 = destination
		self.source = self.area.get( cornername )
		self.destination = destination
		self.angle = angle
		self.suffix = suffix
		self.board = board

	def coord( self, c ):
		d = c - self.source
		return self.destination + d.rot( self.angle )

	def rot( self, angle ):
		return (angle + 10 * self.angle) % 3600

	def name( self, name ):
		return name + self.suffix

	def net( self, nr, name ):
		if self.suffix != "" and nr != 0:
			if name == None:
				name = self.board.net_by_nr[nr].name
			newname = name + self.suffix
			newnr = self.board.clone_net( nr, name, newname )
			return newnr, newname
		return nr, name


class PcbException( Exception ):
	pass


class PcbObject:

	def __init__( self ):
		self.objs = []

	def clone( self, transform=nulltransform ):
		raise PcbException, "subclass must override clone()"

	def add( self, obj ):
		index = len(self.objs)
		self.objs.append( obj )
		return index

	def add_line( self, line, words ):
		"""
		Add a line to this object.

		Returns a tuple containing two boolean values. If the first one is
		True the line has been used, if False the line should be processed
		again. The second boolean indicates if this object is finished
		processing lines.
		"""
		raise PcbException, "subclass '%s' must override add_line()" % \
					self.__class__.__name__

	def write( self, ofd ):
		raise PcbException, "subclass '%s' must override write()" % \
					self.__class__.__name__

	def write_objs( self, ofd ):
		for obj in self.objs:
			obj.write( ofd )


class PcbLineObject( PcbObject ):

	def __init__( self, starttag, endtag, newline ):
		PcbObject.__init__( self )
		self.starttag = starttag
		self.endtag = endtag
		self.newline = newline

	def add_line( self, line, words ):
		if words[0] == self.endtag:
			return ( True, True )
		self.objs.append( line )
		return ( True, False )

	def write( self, ofd ):
		ofd.write( self.starttag + "\n" )
		if len(self.objs) > 0:
			ofd.write( "\n".join( self.objs ) )
			ofd.write( "\n" + self.endtag + "\n" )
		else:
			ofd.write( self.endtag + "\n" )
		if self.newline:
			ofd.write( "\n" )


class PcbListObject( PcbObject ):

	def __init__( self, constructor, starttag, line, words ):
		PcbObject.__init__( self )
		self.constructor = constructor
		self.starttag = starttag
		self.obj = self.constructor( line, words )

	def add_line( self, line, words ):
		if self.obj:
			used, end = self.obj.add_line( line, words )
			if end:
				self.add( self.obj )
				self.obj = None
		elif words[0] == self.starttag:
			self.obj = self.constructor( line, words )
		else:
			return ( False, True )
		return ( True, False )

	def write( self, ofd ):
		self.write_objs( ofd )


class General( PcbLineObject ):

	def __init__( self, line, words ):
		PcbLineObject.__init__( self, "$GENERAL", "$EndGENERAL", True )


class Sheetdescr( PcbLineObject ):

	def __init__( self, line, words ):
		PcbLineObject.__init__( self, "$SHEETDESCR", "$EndSHEETDESCR", True )


class Setup( PcbLineObject ):

	def __init__( self, line, words ):
		PcbLineObject.__init__( self, "$SETUP", "$EndSETUP", True )


class Equipot( PcbObject ):

	def __init__( self, line, words ):
		#PcbLineObject.__init__( self, "$EQUIPOT", "$EndEQUIPOT", False )
		self.netclass = None

	def clone( self, transform=nulltransform ):
		e = Equipot( self, None, None )
		e.nr = self.nr
		e.name = self.name
		e.st1 = self.st1
		return e

	def add_line( self, line, words ):
		if words[0] == "$EndEQUIPOT":
			return ( True, True )
		elif words[0] == "Na":
			self.nr = int(words[1])
			self.name = words[2][1:-1]
		elif words[0] == "St":
			self.st1 = words[1]
		else:
			raise PcbException, "unknown Equipot line '%s'" % words[0]
		return ( True, False )

	def write( self, ofp ):
		ofp.write( "$EQUIPOT\nNa %d \"%s\"\nSt %s\n$EndEQUIPOT\n" % (
				self.nr, self.name, self.st1 ) )


class Equipots( PcbListObject ):

	def __init__( self, line, words ):
		PcbListObject.__init__( self, Equipot, "$EQUIPOT", line, words )


class Nclass( PcbObject ):

	def __init__( self, line, words ):
		PcbObject.__init__( self )
		self.nets = []

	def clone( self, transform=nulltransform ):
		n = Nclass( None, None )
		n.objs = self.objs[:]
		n.nets = self.nets[:]
		return n

	def add_line( self, line, words ):
		if words[0] == "$EndNCLASS":
			return True, True
		elif words[0] == "AddNet":
			self.nets.append( words[1][1:-1] )
		else:
			self.objs.append( line )
		return True, False

	def write( self, ofp ):
		ofp.write( "$NCLASS\n" )
		for line in self.objs:
			ofp.write( "%s\n" % line )
		for net in self.nets:
			ofp.write( "AddNet \"%s\"\n" % net )
		ofp.write( "$EndNCLASS\n" )


class Nclasses( PcbListObject ):

	def __init__( self, line, words ):
		PcbListObject.__init__( self, Nclass, "$NCLASS", line, words )


class Module( PcbObject ):

	def __init__( self, line, words ):
		PcbObject.__init__( self )
		self.name = words[1]
		self.obj = None
		self.lines = []

	def clone( self, transform=nulltransform ):
		m = Module( "", ( "", self.name ) )
		m.position = transform.coord( self.position )
		m.angle = transform.rot( self.angle )
		m.po4 = self.po4
		m.po5 = self.po5
		m.po6 = self.po6
		m.po7 = self.po7
		for line in self.lines:
			if line.startswith( "T0 " ):
				words = line.split()
				words[11] = "\"%s\"" % transform.name( words[11][1:-1] )
				line = " ".join( words )
			m.lines.append( line )
		for obj in self.objs:
			m.add( obj.clone( transform ) )
		return m

	def add_line( self, line, words ):
		if words[0] == "$EndMODULE":
			return ( True, True )
		elif line == "$PAD":
			self.obj = Pad( line, words )
		elif self.obj:
			used, end = self.obj.add_line( line, words )
			if end:
				self.objs.append( self.obj )
				self.obj = None
		elif words[0] == "Po":
			self.position = Coord( int(words[1]), int(words[2]) )
			self.angle = int(words[3])
			self.po4 = words[4]
			self.po5 = words[5]
			self.po6 = words[6]
			self.po7 = words[7]
		else:
			# ++++
			self.lines.append( line )
		return True, False

	def write( self, ofd ):
		ofd.write( "$MODULE %s\n" % self.name )
		ofd.write( "Po %s %d %s %s %s %s\n" % ( self.position.to_str(),
				self.angle, self.po4, self.po5, self.po6, self.po7 ) )
		for line in self.lines:
			ofd.write( line + "\n" )
		self.write_objs( ofd )
		ofd.write( "$EndMODULE  %s\n" % self.name )

	def inside( self, area ):
		return area.inside( self.position )


class Modules( PcbListObject ):

	def __init__( self, line, words ):
		PcbListObject.__init__( self, Module, "$MODULE", line, words )


class Pad( PcbObject ):

	def __init__( self, line, words ):
		#PcbLineObject.__init__( self, "$PAD", "$EndPAD", False )
		self.local = None

	def clone( self, transform=nulltransform ):
		p = Pad( None, None )
		p.name = self.name
		p.sh2 = self.sh2
		p.sh3 = self.sh3
		p.sh4 = self.sh4
		p.sh5 = self.sh5
		p.sh6 = self.sh6
		p.angle = transform.rot( self.angle )
		p.drill = self.drill
		p.at = self.at
		p.netnr, p.netname = transform.net( self.netnr, self.netname )
		p.po = self.po
		p.local = self.local
		return p

	def add_line( self, line, words ):
		if words[0] == "$EndPAD":
			return ( True, True )
		elif words[0] == "Sh":
			self.name = words[1][1:-1]
			self.sh2 = words[2]
			self.sh3 = words[3]
			self.sh4 = words[4]
			self.sh5 = words[5]
			self.sh6 = words[6]
			self.angle = int(words[7])
		elif words[0] == "Dr":
			self.drill = line
		elif words[0] == "At":
			self.at = line
		elif words[0] == "Ne":
			self.netnr = int(words[1])
			self.netname = words[2][1:-1]
		elif words[0] == "Po":
			self.po = line
		elif words[0] == ".LocalClearance":
			if self.local:
				self.local += "\n" + line
			else:
				self.local = line
		return ( True, False )

	def write( self, ofd ):
		ofd.write( "$PAD\n" )
		ofd.write( "Sh \"%s\" %s %s %s %s %s %d\n" % ( self.name,
			self.sh2, self.sh3, self.sh4, self.sh5, self.sh6, self.angle ) )
		ofd.write( self.drill + "\n" )
		ofd.write( self.at + "\n" )
		ofd.write( "Ne %d \"%s\"\n" % ( self.netnr, self.netname ) )
		ofd.write( self.po + "\n" )
		if self.local:
			ofd.write( self.local + "\n" )
		ofd.write( "$EndPAD\n" )


class Drawsegment( PcbLineObject ):

	def __init__( self, line, words ):
		PcbLineObject.__init__( self, "$DRAWSEGMENT", "$EndDRAWSEGMENT", False )


class Drawsegments( PcbListObject ):

	def __init__( self, line, words ):
		PcbListObject.__init__( self, Drawsegment, "$DRAWSEGMENT", line, words )


class Textpcb( PcbObject ):

	def __init__( self, line, words ):
		#PcbLineObject.__init__( self, "$TEXTPCB", "$EndTEXTPCB", False )
		pass

	def clone( self, transform=nulltransform ):
		t = Textpcb( None, None )
		t.text = self.text
		t.position = transform.coord( self.position )
		t.charwidth = self.charwidth
		t.charheight = self.charheight
		t.linewidth = self.linewidth
		t.angle = transform.rot( self.angle )
		t.de = self.de
		return t

	def add_line( self, line, words ):
		if words[0] == "$EndTEXTPCB":
			return True, True
		elif words[0] == "Te":
			self.text = line.split( "\"" )[1]
		elif words[0] == "nl":
			self.text += "\n" + line.split( "\"" )[1]
		elif words[0] == "Po":
			self.position = Coord( int(words[1]), int(words[2]) )
			self.charwidth = int(words[3])
			self.charheight = int(words[4])
			self.linewidth = int(words[5])
			self.angle = int(words[6])
		elif words[0] == "De":
			self.de = line
		return True, False

	def write( self, ofd ):
		ofd.write( "$TEXTPCB\n" )
		ofd.write( "Te \"%s\"\n" % self.text.replace( "\n", "\"\nnl \"" ) )
		ofd.write( "Po %s %d %d %d %d\n" % ( self.position.to_str(),
				self.charwidth, self.charheight, self.linewidth, self.angle ) )
		ofd.write( self.de + "\n" )
		ofd.write( "$EndTEXTPCB\n" )

	def inside( self, area ):
		return area.inside( self.position )


class Textpcbs( PcbListObject ):

	def __init__( self, line, words ):
		PcbListObject.__init__( self, Textpcb, "$TEXTPCB", line, words )


class Cotation( PcbLineObject ):

	def __init__( self, line, words ):
		PcbLineObject.__init__( self, "$COTATION", "$endCOTATION", False )


class Cotations( PcbListObject ):

	def __init__( self, line, words ):
		PcbListObject.__init__( self, Cotation, "$COTATION", line, words )


class Track( PcbObject ):

	def __init__( self, line, words ):
		PcbObject.__init__( self )
		if words != None:
			self.po1 = int(words[1])
			self.coord1 = Coord( int(words[2]), int(words[3]) )
			self.coord2 = Coord( int(words[4]), int(words[5]) )
			self.width = int(words[6])
			self.po7 = int(words[7])

	def clone( self, transform=nulltransform ):
		t = Track( None, None )
		t.po1 = self.po1
		t.coord1 = transform.coord( self.coord1 )
		t.coord2 = transform.coord( self.coord2 )
		t.width = self.width
		t.po7 = self.po7
		t.layer = self.layer
		t.de2 = self.de2
		#t.de3 = self.de3
		t.de3 = "%d" % transform.net( int(self.de3), None )[0]
		t.de4 = self.de4
		t.de5 = self.de5
		return t

	def add_line( self, line, words ):
		if words[0] != "De":
			print "unrecognized line in Track:\n    %s" % line
			raise PcbException, "unrecognized line in Track: %s" % line
		self.layer = int(words[1])
		self.de2 = words[2]
		self.de3 = words[3]
		self.de4 = words[4]
		self.de5 = words[5]
		return True, True

	def write( self, ofd ):
		ofd.write( "Po %d %s %s %d %d\n" % ( self.po1,
				self.coord1.to_str(), self.coord2.to_str(),
				self.width, self.po7 ) )
		ofd.write( "De %d %s %s %s %s\n" % ( self.layer,
				self.de2, self.de3, self.de4, self.de5 ) )

	def inside( self, area ):
		return area.inside( self.coord1 ) and area.inside( self.coord2 )


class Tracks( PcbObject ):

	def __init__( self, line, words ):
		PcbObject.__init__( self )

	def add_line( self, line, words ):
		if words[0] == "$EndTRACK":
			return ( True, True )
		elif words[0] == "Po":
			self.add( Track( line, words ) )
		else:
			self.objs[-1].add_line( line, words )
		return True, False

	def write( self, ofd ):
		ofd.write( "$TRACK\n" )
		self.write_objs( ofd )
		ofd.write( "$EndTRACK\n" )


class Zone( PcbLineObject ):

	def __init__( self, line, words ):
		PcbLineObject.__init__( self, "$ZONE", "$EndZONE", False )


class CzoneOutline( PcbObject ):

	def __init__( self, line, words ):
		PcbObject.__init__( self )
		self.lines = []
		self.in_polyscorners = False
		self.polyscorners = []

	def clone( self, transform=nulltransform ):
		o = CzoneOutline( None, None )
		o.zinfo1 = self.zinfo1
		o.netnr, o.netname = transform.net( self.netnr, self.netname )
		o.lines = self.lines[:]
		for c, a in self.objs:
			o.add( ( transform.coord( c ), a ) )
		for c, a, b in self.polyscorners:
			o.polyscorners.append( ( transform.coord( c ), a, b ) )
		return o

	def add_line( self, line, words ):
		if words[0] == "$endCZONE_OUTLINE":
			return True, True
		elif words[0] == "$POLYSCORNERS":
			self.in_polyscorners = True
		elif words[0] == "$endPOLYSCORNERS":
			self.in_polyscorners = False
		elif self.in_polyscorners:
			self.polyscorners.append( ( Coord( int(words[0]), int(words[1]) ),
					int(words[2]), int(words[3]) ) )
		elif words[0] == "ZCorner":
			self.add( ( Coord( int(words[1]), int(words[2]) ), int(words[3]) ) )
		elif words[0] == "ZInfo":
			self.zinfo1 = words[1]
			self.netnr = int(words[2])
			self.netname = words[3][1:-1]
		else:
			self.lines.append( line )
		return True, False

	def write( self, ofd ):
		ofd.write( "$CZONE_OUTLINE\n" )
		ofd.write( "ZInfo %s %d \"%s\"\n" % ( self.zinfo1,
				self.netnr, self.netname ) )
		for line in self.lines:
			ofd.write( line + "\n" )
		for c, a in self.objs:
			ofd.write( "ZCorner %s %d\n" % ( c.to_str(), a ) )
		if len(self.polyscorners) > 0:
			ofd.write( "$POLYSCORNERS\n" )
			for c, a, b in self.polyscorners:
				ofd.write( "%s %d %d\n" % ( c.to_str(), a, b ) )
			ofd.write( "$endPOLYSCORNERS\n" )
		ofd.write( "$endCZONE_OUTLINE\n" )

	def inside( self, area ):
		#print "area:", area.tl.to_str(), area.br.to_str()
		for c, a in self.objs:
			#print "zone:", c.to_str(), area.inside( c )
			if not area.inside( c ):
				return False
		return True


class CzoneOutlines( PcbListObject ):

	def __init__( self, line, words ):
		PcbListObject.__init__( self, CzoneOutline, "$CZONE_OUTLINE", line, words )


class Polyscorners( PcbLineObject ):

	def __init__( self, line, words ):
		PcbLineObject.__init__( self, "$POLYSCORNERS", "$endPOLYSCORNERS", False )





class Board( PcbObject ):

	def __init__( self ):
		PcbObject.__init__( self )
		self.clear()

	def clear( self ):
		self.shebang = "PCBNEW-BOARD Version 1 date xxx"
		self.createdby = "# Created by panelize.py V0.1"
		self.typeindex = {}
		self.sourcearea = Area( Coord( 0, 0 ), Coord( 0, 0 ) )
		self.transforms = 0
		self.next_net_nr = 0
		self.net_by_nr = {}
		self.net_by_name = {}

	def read_file( self, filename ):
		self.clear()
		starttags = {
			"$GENERAL": ( "general", General, ),
			"$SHEETDESCR": ( "sheetdescr", Sheetdescr, ),
			"$SETUP": ( "setup", Setup, ),
			"$EQUIPOT": ( "equipot", Equipots, ),
			"$NCLASS": ( "nclass", Nclasses, ),
			"$MODULE": ( "module", Modules, ),
			"$DRAWSEGMENT": ( "drawsegment", Drawsegments, ),
			"$TEXTPCB": ( "textpcb", Textpcbs, ),
			"$COTATION": ( "cotation", Cotations, ),
			"$TRACK": ( "track", Tracks, ),
			"$ZONE": ( "zone", Zone, ),
			"$CZONE_OUTLINE": ( "czone_outline", CzoneOutlines, ),
		}
		ifd = open( filename, "r" )
		obj = None
		hmms = 10
		try:
			line = ifd.next().rstrip()
			while True:
				line_used = True
				#print "   ", line[:60]
				words = line.split()
				if line == "" or line[0] == "#":
					pass
				elif obj:
					line_used, end = obj.add_line( line, words )
					if end:
						obj = None
						#print "END"
				elif words[0] in starttags:
					typename, constr = starttags[words[0]]
					if typename in self.typeindex:
						#print "reuse", line
						obj = self.objs[self.typeindex[typename]]
						line_used = False
					else:
						#print "add", line
						obj = constr( line, words )
						self.typeindex[typename] = self.add( obj )
				elif words[0] == "PCBNEW-BOARD":
					#print "shebang"
					self.shebang = line
				elif words[0] == "$EndBOARD":
					#print "EndBOARD"
					try:
						line = ifd.next().rstrip()
						raise PcbException, "missing EOF."
					except StopIteration:
						break
				else:
					print "hmm?", line
					hmms -= 1
					if hmms <= 0:
						break
				if line_used:
					line = ifd.next().rstrip()
		except StopIteration:
			print "unexpected EOF"
			raise PcbException, "unexpected EOF."
		ifd.close()
		print "loaded."
		for net in self.objs[self.typeindex["equipot"]].objs:
			self.net_by_nr[net.nr] = net
			self.net_by_name[net.name] = net.nr
			#print "net", net.nr, net.name
			if net.nr >= self.next_net_nr:
				self.next_net_nr = net.nr + 1
		for netclass in self.objs[self.typeindex["nclass"]].objs:
			for netname in netclass.nets:
				self.net_by_nr[self.net_by_name[netname]].netclass = netclass


	def write_file( self, filename ):
		ofd = open( filename, "w" )
		self.write( ofd )
		ofd.close()

	def write( self, ofd ):
		ofd.write( "%s\n\n%s\n\n" % ( self.shebang, self.createdby ) )
		self.write_objs( ofd )
		ofd.write( "$EndBOARD\n" )

	def clone_net( self, nr, name, newname ):
		if name == newname:
			return nr
		if not nr in self.net_by_nr:
			raise PcbException, "invalid net nr"
		oldnet = self.net_by_nr[nr]
		if oldnet.name != name:
			raise PcbException, "net nr/name mismatch"
		if nr == 0 and name != newname:
			raise PcbException, "net nr 0 can't be cloned"
		if not newname in self.net_by_name:
			newnr = self.next_net_nr
			self.next_net_nr += 1
			newnet = Equipot( None, None )
			newnet.nr = newnr
			newnet.name = newname
			newnet.st1 = oldnet.st1
			newnet.netclass = oldnet.netclass
			newnet.netclass.nets.append( newname )
			self.net_by_nr[newnr] = newnet
			self.net_by_name[newname] = newnr
		return self.net_by_name[newname]

	def source_area( self, area ):
		self.sourcearea = area

	def copy( self, destination ):
		self.rotate( destination, "top-left", 0 )

	def rotate( self, destination, cornername, angle ):
		self.transforms += 1
		suffix = "_C%d" % self.transforms
		trans = RotateTransform( self.sourcearea, cornername,
				destination, angle, suffix, self )
		copytypes = ( "module", "textpcb", "track", "czone_outline" )
		for typename in copytypes:
			container = self.objs[self.typeindex[typename]]
			add = []
			for obj in container.objs:
				if obj.inside( self.sourcearea ):
					add.append( obj.clone( trans ) )
			container.objs += add


def cmd_source_area( board, topleft, bottomright ):
	board.source_area( Area( topleft, bottomright ) )

def cmd_copy( board, destination ):
	cmd_rotate( board, destination, "top-left", 0 )

def cmd_rotate( board, coord, cornername, angle ):
	board.rotate( coord, cornername, angle )
	
def usage( nil ):
	global commands
	print "panelize.py V1.0 for kicad brd files."
	print
	print "usage: infile outfile commands..."
	print
	print "commands:"
	cmdnames = commands.keys()[:]
	cmdnames.sort()
	for cmdname in cmdnames:
		func, cmddescr, args = commands[cmdname]
		line = "  %s" % cmdname
		for type, name, descr in args:
			line += " <%s>" % name
		print
		print line
		print
		print "      %s" % cmddescr
		if len(args) > 0:
			print
			for type, name, descr in args:
				descs = descr.split( "\n" )
				print "      %-15s %s" % ( name, descs[0] )
				for d in descs[1:]:
					print "      %-15s %s" % ( "", d )
	print
	sys.exit( 0 )

commands = {
	"source-area": ( cmd_source_area,
		"Set the source area to copy.",
		(
			( "coord", "top-left", "Coordinate of corner (X/Y)." ),
			( "coord", "bottom-right", "Coordinate of corner (X/Y)." ),
	) ),
	"copy": ( cmd_copy,
		"Copy source are to destination.",
		(
			( "coord", "destination", "Coordinate of top-left corner (X/Y)." ),
	) ),
	"rotate": ( cmd_rotate,
		"Copy source are to destination and rotate it.",
		(
			( "coord", "destination", "Coordinate of destination corner (X/Y)." ),
			( "corner", "source-corner",
				"Corner of source area which maps to destination." +
				"\n(top-left|top-right|bottom-left|bottom-right)" ),
			( "angle", "angle", "Rotation angle (0|90|180|270)." ),
	) ),
	"help": ( usage,
		"Print this help text.",
		[]
	),
}

def panelize( infile, outfile, args ):
	global commands
	board = Board()
	board.read_file( infile )
	while len(args) > 0:
		cmd = args[0]
		args = args[1:]
		if cmd in commands:
			function, descr, argtypes = commands[cmd]
			if len(args) < len(argtypes):
				print "missing arguments for command '%s'." % cmd
				return 1
			cmdargs = []
			for i in range( 0, len(argtypes) ):
				type = argtypes[i][0]
				if type == "coord":
					try:
						cmdargs.append( Coord( None, None, args[i], "/" ) )
					except:
						return 1
				elif type == "corner":
					if not args[i] in ( "top-left", "top-right", "bottom-left", "bottom-right" ):
						print "invalid corner name '%s'" % args[i]
						return 1
					cmdargs.append( args[i] )
				elif type == "angle":
					if not (args[i].isdigit() or 
							(args[i][0] == "-" and args[i][1:].isdigit()) ):
						print "invalid angle name '%s'" % args[i]
						return 1
					a = (int(args[i]) % 360 + 360) % 360
					if not a in ( 0, 90, 180, 270 ):
						print "angle must be a multiple of 90"
						return 1
					cmdargs.append( a )
				else:
					print "unhandled type '%s'" % type
					return 1
			print "%s." % cmd
			function( board, *cmdargs )
			args = args[len(argtypes):]
		else:
			print "unknown command '%s'." % cmd
			return 1
	board.write_file( outfile )
	print "saved."
	return 0

if __name__ == "__main__":
	if len(sys.argv) < 3:
		usage( None )
	else:
		infile = sys.argv[1]
		outfile = sys.argv[2]
		args = sys.argv[3:]
		sys.exit( panelize( infile, outfile, args ) )

