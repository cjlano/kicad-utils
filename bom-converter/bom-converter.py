#!/usr/bin/python3
# Parses and converts bom files in xml format exported with kicad
# @author: Simon Gansen

import argparse

from xmlBom import *
from htmlBom import *
from csvBom import *

if __name__ == "__main__":

    # parse arguments
    argparser = argparse.ArgumentParser(description='Converts a kicad bom given in XML format to HTML.')
    argparser.add_argument('infile', help='XML file exported by eeschema (kicad)')
    argparser.add_argument('htmlfile', nargs='?', help='HTML output file')
    argparser.add_argument('--csv', dest='csv_output', nargs='?', help='CSV output file')
    args = argparser.parse_args()

    # default html output file name
    if args.htmlfile is None:
        args.htmlfile = args.infile + '.html'

    # load xml file
    xml_bom = XmlBom()
    xml_bom.load(args.infile)
    xml_bom.merge_similar()
    xml_bom.count()
    xml_bom.sort()

    # if required, create a csv file
    if args.csv_output:
        csv_bom = CsvBom(xml_bom)
        csv = csv_bom.get_csv_string()
        with open(args.csv_output, 'w') as csv_file:
            csv_file.write(csv)
            print('*** CSV file', csv_file.name, 'written')

    # create html string
    html_bom = HtmlBom(xml_bom)
    html = html_bom.get_html_string()

    # write html to file
    with open(args.htmlfile, 'w') as html_file:
        html_file.write(html)
        print('*** HTML file ' + html_file.name + ' written')
