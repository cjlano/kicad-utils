#!/usr/bin/python3
# @author: Simon Gansen

import os
import re
from operator import itemgetter

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

class XmlBom(object):
    """
    Manages parsing and preparation of the input XML file
    """

    def __init__(self):
        self.title = ''
        self.components = []
        self.filename = ''

    def __str__(self):
        self.count()
        out = ''
        for c in self.components:
            out += str(c['qty']) + 'x\t'
            for d in c['designators']:
                out += d + ' '
            out += '\t' + c['value'] + '\t' + c['footprint'] + '\n';
        return out

    def load(self, filename):
        print('*** Parsing input file ...')
        self.filename = filename
        xml_tree = etree.parse(filename)
        xml_root = xml_tree.getroot()

        # parse xml
        for comp in xml_root.iter('comp'):
            # write component into dictionary
            component = {}
            component['designators'] = [comp.attrib['ref']] # designators key contains list
            component['value'] = '' if comp.find('value') is None else comp.find('value').text.strip()
            component['footprint'] = '' if comp.find('footprint') is None else comp.find('footprint').text.strip()
            component['datasheet'] = '' if comp.find('datasheet') is None else comp.find('datasheet').text.strip()

            fields = comp.find('fields');
            if fields is not None:
                for field in fields.iter('field'):
                    component[field.attrib['name']] = field.text.strip()

            # add dictionary to list
            self.components.append(component)

        # set title from filename
            self.title = os.path.splitext(filename)[0]

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
                        if key in m and key in c:
                            match = True
                            print('Empty field', key, 'in', c['designators'][0])
                        elif not key in m and not key in c:
                            match = True
                            print('Missing field' , key, 'in', c['designators'][0])
                        else:
                            match = False
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
        print('Found', len(merged_components),'unique component types in', self.filename)
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
