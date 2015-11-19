#!/usr/bin/python3
# @author: Simon Gansen

from xmlBom import *

class HtmlBom(object):
    """
    Generates HTML from a given XmlBom object
    """

    def __init__(self, xml_bom):
        self.xml_bom = xml_bom

    def get_html_string(self):
        print('*** Generating HTML ...')

        # header, style sheets and table start
        html = ''
        html += "<!DOCTYPE html>\n";
        html += '<html lang=\"en\">\n'
        html += '<head>\n'
        html += '\t<meta charset=\"utf-8\">\n'
        html += '\t<title>Kicad BOM</title>\n'
        html += '\t<style media=\"screen\" type=\"text/css\">\n'
        html += '\t\tbody { font-family: monospace; }\n'
        html += '\t\th1 { text-decoration: underline }\n'
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
        html += '\t\t\t<th colspan=\"10\"><h1>' + self.xml_bom.title + '</h1></th>\n'
        html += '\t\t</tr>\n'
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
