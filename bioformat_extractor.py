import pyclowder
import re
import logging
import tempfile
import os
import subprocess

from pyclowder.extractors import Extractor
import pyclowder.files

import javabridge
import bioformats.formatreader


javabridge.start_vm(class_path=bioformats.JARS)


class BioformatExtractor(Extractor):
    def __init__(self):
        Extractor.__init__(self)

        # add any additional arguments to parser
        # self.parser.add_argument('--max', '-m', type=int, nargs='?', default=-1,
        #                          help='maximum number (default=-1)')

        # parse command line and load default logging configuration
        self.setup()

        # setup logging for the exctractor
        logging.getLogger('pyclowder').setLevel(logging.DEBUG)
        logging.getLogger('__main__').setLevel(logging.DEBUG)

    def get_info(self, obj):
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

    def process_message(self, connector, host, secret_key, resource, parameters):
        # Process the file and upload the results

        logger = logging.getLogger(__name__)
        inputfile = resource["local_paths"][0]
        file_id = resource['id']

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
            result['pixel'] = self.get_info(pixels)

            metadata = self.get_metadata(result, 'file', file_id, host)
            logger.debug(metadata)
            # upload metadata
            pyclowder.files.upload_metadata(connector, host, secret_key, file_id, metadata)

        except Exception as e:
            logger.error("Error getting metadata from file", e)


if __name__ == "__main__":
    extractor = BioformatExtractor()
    extractor.start()
