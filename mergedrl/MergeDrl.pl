#!/usr/bin/perl -w

# MergeDrl.pl
#
# CC-BY 2012 9DOF <9dof.gg@gmail.com>
#
# Merges several Excellon format drill files into a single file.
#
# Usage: MergeDrl.pl input_file [...] > output_file
#
# Output's header will be copied from first input file

use strict;

use IO::File;

use Data::Dumper;

sub parseExcellon($);

# Get arguments
my @drills;

# Parse args and dump content
foreach my $fn (@ARGV) {
  push @drills, parseExcellon($fn);
#  my $f = new IO::File($fn, 'r');
#  print 'Dumping ', $fn, "\n";
#  dumpExcellon($f);
}

#print Dumper(\@drills);

# Combine drills
my %mergedDrills = (
  tools => {},
  coords => {});

my @comboTools = ();
foreach my $t(@drills) {
  while (my($k,$v)=each %{$t->{tools}}){
    push @comboTools, {spec => $v, coords => $t->{coords}->{$k}};
  }
}

#print "Combo:\n";
#print Dumper(\@comboTools);

# Sort spec and allocate new indices
my $currTool;
my $prevTool;
my $currIndex = 1;
my @finalTools = ();

foreach my $e(sort {$a->{spec} cmp $b->{spec}} @comboTools) {
  # Check if same spec as last one
  if ($prevTool && $prevTool->{spec} eq $e->{spec}) {
    push @{$prevTool->{coords}}, @{$e->{coords}};
  } else {
    $e->{tool} = 'T'.$currIndex++;
    $prevTool = $e;
    push @finalTools, $prevTool;
  }
}
#  print Dumper(\@finalTools);

# Output result
local $/ = "\r\n";
# Header
print "M48$/";
foreach my $h(@{$drills[0]->{headers}}) {
  print "$h$/";
}
# List of tools
foreach my $t(@finalTools) {
  print $t->{tool}.$t->{spec}.$/;
}
# End of header
print "\%$/";
# Body
print "G90$/";
print "G05$/";
print "M72$/";
# Coords
foreach my $t(@finalTools) {
  print $t->{tool}, $/;
  foreach my $c(@{$t->{coords}}) {
    print "$c$/";
  }
}
# End
print "T0$/";
print "M30$/";

exit 0;

# Excellon parser
sub parseExcellon($) {
  my ($fn) = @_;
  my %res = (
    filename => $fn,
    tools => {},
    coords => {},
    headers => []);

  my $f = new IO::File($fn, 'r');

  my $inHeader = 0;
  my $inBody = 0;
  my $currTool;
#  print "Inside parseExcellon(${fn})\n";
  while(<$f>){
    local $/ = "\r\n";
    chomp;
#    chop;	# input is MSDOS line terminated
    if (!$inHeader && !$inBody) {	# Search for start of header (^M48)
      if (/^M48/) {
        # Found start of header
        $inHeader = 1;
      } else {
#        print 's';
      }
    } elsif ($inHeader) {	# Inside header, collect info until end of header (^%)
      if (!/^\%/) {
#        print 'h';
        if (/^(T\d+)(.*)/) {
          $res{tools}->{$1} = $2;
          $res{coords}->{$1} = [];
        } else {
          push @{$res{headers}}, $_;
        }
      } else {
        $inHeader = 0;
        $inBody = 1;
      }
    } elsif ($inBody) {	# Inside body, collect coords until end of body (^M30)
      if (!/^M30/) {
#        print 'b';
        if (/^(T\d+)/) {
          $currTool = $1;
        } elsif ($currTool && exists $res{coords}->{$currTool}) {
          push @{$res{coords}->{$currTool}}, $_;
        }
      } else {
        $inBody = 0;
#        print "\n";
        last;
      }
    }
  }
  $f->close;
  # Dump info
#  print "Info dump\n";
#  print "Headers:\n";
#  print @headers;
#  print "Tools:\n";
#  print join(",", @tools), "\n";
#  print "Coords:\n";
#  foreach my $t(@tools) {
#    print "Tool: ", $t, "\n";
#    print @{$coords{$t}};
    \%res;
  }

