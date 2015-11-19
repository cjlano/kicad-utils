#!/usr/bin/python3
# @author: Simon Gansen

class CsvBom(object):
    """
    Generates CSV (that can be imported by certain suppliers) from a given XmlBom object
    """

    def __init__(self, xml_bom):
        self.xml_bom = xml_bom

    def get_csv_string(self):
        print('*** Generating CSV for', len(self.xml_bom.components), 'unique component types')
        row_count = 0
        seperator = ', '
        csv = 'QTY,\tSupplier Part Number,\tManufacturer Part Number\n'
        for c in self.xml_bom.components:
            try:
                row_sequence = (str(c['qty']), c['Supplier Part Number'], c['Manufacturer Part Number'])
                row = seperator.join(row_sequence)
                csv += row + '\n'
                row_count += 1
            except KeyError as exc:
                print('Ignoring', c['designators'], 'due to missing key(s) named', exc.args[0])

        print('Added', str(row_count), 'rows')
        return csv
