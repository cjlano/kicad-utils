#!/usr/bin/python3
# Parses and converts bom files in xml format exported with kicad
# @author: Simon Gansen

import argparse
import re
from operator import itemgetter

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

class XmlBom(object):
    """Manages parsing and preparation of the input XML file"""

    def __init__(self):
        self.components = []

    def __str__(self):
        out = ''
        for c in self.components:
            out += str(c['qty']) + 'x\t'
            for d in c['designators']:
                out += d + ' '
            out += '\t' + c['value'] + '\t' + c['footprint'] + '\n';
        return out

    def load(self, filename):
        xml_tree = etree.parse(filename)
        xml_root = xml_tree.getroot()

        for comp in xml_root.iter('comp'):
            # write component into dictionary
            component = {}
            component['designators'] = [comp.attrib['ref']] # designators key contains list
            component['value'] = "" if comp.find('value') is None else comp.find('value').text
            component['footprint'] = "" if comp.find('footprint') is None else comp.find('footprint').text
            component['datasheet'] = "" if comp.find('datasheet') is None else comp.find('datasheet').text

            fields = comp.find('fields');
            if fields is not None:
                for field in fields.iter('field'):
                    component[field.attrib['name']] = field.text

            # add dictionary to list
            self.components.append(component)

    def merge_similar(self):
        merged_components = []

        # traverse all components
        for c in self.components:
            merged = False

            # try to find matching component
            for m in merged_components:

                # compare all fields
                match = True;
                for key in ['value', 'footprint', 'datasheet', 'Supplier', 'Supplier Part Number',
                            'Supplier Link', 'Manufacturer', 'Manufacturer Part Number']:
                    try:
                        if m[key] != c[key]:
                            match = False
                            break
                    except KeyError:
                        match = False
                        print('Missing field ', key, ' in ', c['designators'][0])
                        break

                # merge to matching component
                if match:
                    m['designators'].append(c['designators'][0])
                    merged = True
                    break

            # append to temporary list if not already merged
            if not merged:
                merged_components.append(c)

        # replace global list
        self.components = merged_components

    def count(self):
        for c in self.components:
            c['qty'] = len(c['designators'])

    def sort(self):
        # sort designators
        for c in self.components:
            c['designators'] = sorted(c['designators'], key=self.natural_sort_key)

        # sort lines
        self.components = sorted(self.components, key=itemgetter('designators'))

    def natural_sort_key(self, string_):
        return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]


class HtmlBom(object):
    """Generates HTML from a given XmlBom object"""

    def __init__(self, xml_bom):
        self.xml_bom = xml_bom

    def get_html_string(self):

        # header, style sheets and table start
        html = ''
        html += "<!DOCTYPE html>\n";
        html += '<html lang=\"en\">\n'
        html += '<head>\n'
        html += '\t<meta charset=\"utf-8\">\n'
        html += '\t<title>Kicad BOM</title>\n'
        html += '\t<style media=\"screen\" type=\"text/css\">\n'
        html += '\t\tbody { font-family: monospace; }\n'
        html += '\t\ttable { border-collapse: collapse; width: 100%; }\n'
        html += '\t\tth { border: 1px solid darkgrey; padding: 1em; background-color: lightgreen; }\n'
        html += '\t\ttd { border: 1px solid darkgrey; padding: 1em; }\n'
        html += '\t\ta:link, a:visited { font-weight: bold; text-decoration: none;'
        html +=                         'color: white; background-color: yellowgreen; }\n'
        html += '\t\ta:active, a:hover { font-weigth: bold;  text-decoration: none;'
        html +=                         'color: yellowgreen; background-color: black; }\n'
        html += '\t</style>\n'
        html += '</head>\n'
        html += '<body>\n'
        html += '\t<table>\n'
        html += '\t\t<tr>\n'
        html += '\t\t\t<th rowspan=\"2\">Designators</th>\n'
        html += '\t\t\t<th rowspan=\"2\">Quantity</th>\n'
        html += '\t\t\t<th rowspan=\"2\">Value</th>\n'
        html += '\t\t\t<th rowspan=\"2\">Footprint</th>\n'
        html += '\t\t\t<th rowspan=\"2\">Datasheet</th>\n'
        html += '\t\t\t<th colspan=\"3\">Supplier</th>\n'
        html += '\t\t\t<th colspan=\"2\">Manufacturer</th>\n'
        html += '\t\t</tr>\n'
        html += '\t\t<tr>\n'
        html += '\t\t\t<th>Name</th>\n'
        html += '\t\t\t<th>Part Number</th>\n'
        html += '\t\t\t<th>Link</th>\n'
        html += '\t\t\t<th>Name</th>\n'
        html += '\t\t\t<th>Part Number</th>\n'
        html += '\t\t</tr>\n'

        # components
        for c in self.xml_bom.components:
            html += '\t\t<tr>\n'

            # designators
            html += '\t\t\t<td>'
            for d in c['designators']:
                html += d + ' '
            html += '</td>\n'

            # base properties
            html += '\t\t\t<td>' + str(c['qty']) +'</td>\n'
            html += '\t\t\t<td>' + c['value'] +'</td>\n'
            html += '\t\t\t<td>' + c['footprint'] +'</td>\n'

            # custom fields
            for key in ['datasheet', 'Supplier', 'Supplier Part Number', 'Supplier Link',
                        'Manufacturer', 'Manufacturer Part Number']:

                try:
                    # link format
                    if key == 'Supplier Link' or key == 'datasheet':
                        html += '\t\t\t<td><a href=\"' + c[key] + '\">[>]</a></td>\n'
                    # normal text
                    else:
                        html += '\t\t\t<td>' + c[key] + '</td>\n'

                # field is empty
                except KeyError:
                    html += '\t\t\t<td></td>\n'

            html += '\t\t</tr>\n'

        
        html += '\t</table>\n'
        html += '<p>Created with bom-converter.py, see https://github.com/theFork/kicad-scripts</p>\n'
        html += '</body>\n'
        html += '</html>\n'
        return html


if __name__ == "__main__":

    # parse arguments
    argparser = argparse.ArgumentParser(description='Converts a kicad bom given in XML format to HTML.')
    argparser.add_argument('infile')
    argparser.add_argument('outfile', nargs='?')
    args = argparser.parse_args()

    # default output file name
    if args.outfile is None:
        args.outfile = args.infile + '.html'

    # load xml file
    xml_bom = XmlBom()
    xml_bom.load(args.infile)
    xml_bom.merge_similar()
    xml_bom.count()
    xml_bom.sort()

    # create html string
    html_bom = HtmlBom(xml_bom)
    html = html_bom.get_html_string()

    # write to file
    with open(args.outfile, 'w') as outfile:
        outfile.write(html)
        print('HTML file ' + outfile.name + ' written')
