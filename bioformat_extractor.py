import pyclowder
import re
import logging
import tempfile
import os, json
import subprocess
import csv
from pyclowder.extractors import Extractor
import pyclowder.files

import javabridge
import bioformats.formatreader


javabridge.start_vm(class_path=bioformats.JARS)

def get_good_bioformats():
    l = dict()
    with open("bioformats.tsv") as fd:
        rd = csv.reader(fd, delimiter="\t", quotechar='"')
        next(rd, None) # skip header
        for row in rd:
            _format = row[0]
            _extensions = row[1]
            _pixels_quality = int(row[2].split('-')[0].strip())
            _metadata_quality = int(row[3].split('-')[0].strip())
            if _pixels_quality >= 3 and _metadata_quality >=3:
                l[_format] = _extensions
    extensions = []
    for _value in l.values():
        extensions.extend(_value.split(','))
    return extensions


def get_info(obj):
    attr = dict()
    type_name = type(obj).__name__
    prop_names = dir(obj)
    for prop_name in prop_names:
        prop_val = getattr(obj, prop_name)
        prop_val_type_name = type(prop_val).__name__
        if prop_val_type_name in [ 'method', 'method-wrapper', 'type', 'NoneType', 'builtin_function_or_method', 'dict']:
            pass
        try:
            val_as_str = json.dumps([ prop_val ], indent=2)[1:-1]
            attr[prop_name] = val_as_str.strip()
        except:
            pass
    return attr

class BioformatExtractor(Extractor):
    def __init__(self):
        Extractor.__init__(self)

        # add any additional arguments to parser
        # self.parser.add_argument('--max', '-m', type=int, nargs='?', default=-1,
        #                          help='maximum number (default=-1)')

        # parse command line and load default logging configuration
        self.setup()
        self.bioformat_extensions = get_good_bioformats()
        # setup logging for the exctractor
        logging.getLogger('pyclowder').setLevel(logging.DEBUG)
        logging.getLogger('__main__').setLevel(logging.DEBUG)

        
    def process_message(self, connector, host, secret_key, resource, parameters):
        # Process the file and upload the results

        logger = logging.getLogger(__name__)
        inputfile = resource["local_paths"][0]
        file_id = resource['id']
        filename, file_extension = os.path.splitext(inputfile)
        if file_extension in self.bioformat_extensions:
            #this part handles the metadata
            try:
                result = dict()
                omexmlstr=bioformats.get_omexml_metadata(inputfile)
                o=bioformats.OMEXML(omexmlstr)
                #
                result['Name'] = o.get_Name()
                result['AcquisitionDate'] = o.get_AcquisitionDate()
                result['ID'] = o.get_ID()
                result['ns'] = o.ns
                # pixel infor
                pixels=o.image().Pixels()
                result['pixel'] = get_info(pixels)

                metadata = self.get_metadata(result, 'file', file_id, host)
                logger.debug(metadata)
                # upload metadata
                pyclowder.files.upload_metadata(connector, host, secret_key, file_id, metadata)

            except Exception as e:
                logger.error("Error getting metadata from file", e)
        else:
            logger.error(f"File format not supprted, Supported list:{self.bioformat_extensions}")
        


if __name__ == "__main__":
    extractor = BioformatExtractor()
    extractor.start()
