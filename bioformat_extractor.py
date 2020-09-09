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

from xml.dom.minidom import parseString

def get_good_bioformats(filepath="/home/bioformats.tsv"):
    l = dict()
    with open(filepath) as fd:
        rd = csv.reader(fd, delimiter="\t", quotechar='"')
        next(rd, None) # skip header
        for row in rd:
            _format = row[0]
            _extensionstr = row[1]
            _pixels_quality = int(row[2].split('-')[0].strip())
            _metadata_quality = int(row[3].split('-')[0].strip())
            if _pixels_quality >= 3 and _metadata_quality >=3:
                _exts = _extensionstr.split(',')
                _extensions = []
                for _ext in _exts:
                    _ext_strip = _ext.strip()
                    if _ext_strip != '' and _ext_strip.startswith("."):
                        _extensions.append(_ext.strip())
                l[_format] = _extensions
    extensions = []
    for _value in l.values():
        extensions.extend(_value)
    return extensions


def get_info(obj):
    attr = dict()
    type_name = type(obj).__name__
    prop_names = dir(obj)
    for prop_name in prop_names:
        prop_val = getattr(obj, prop_name)
        prop_val_type_name = type(prop_val).__name__
        if prop_val_type_name in [ 'method', 'method-wrapper', 'type', 'NoneType', 'builtin_function_or_method', 'dict', '__weakref__', '__module__', '__doc__']:
            pass
        try:
            val_as_str = json.dumps([ prop_val ], indent=2)[1:-1]
            attr[prop_name] = val_as_str.strip()
        except:
            pass
    return attr

def parse_element(element):
    dict_data = dict()
    if element.nodeType == element.TEXT_NODE:
        dict_data['data'] = element.data
    if element.nodeType not in [element.TEXT_NODE, element.DOCUMENT_NODE, 
                                element.DOCUMENT_TYPE_NODE]:
        for item in element.attributes.items():
            dict_data[item[0]] = item[1]
    if element.nodeType not in [element.TEXT_NODE, element.DOCUMENT_TYPE_NODE]:
        for child in element.childNodes:
            child_name, child_dict = parse_element(child)
            if child_name in dict_data:
                try:
                    dict_data[child_name].append(child_dict)
                except AttributeError:
                    dict_data[child_name] = [dict_data[child_name], child_dict]
            else:
                dict_data[child_name] = child_dict 
    return element.nodeName, dict_data

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
                omexmlstr=bioformats.get_omexml_metadata(inputfile)
                dom = parseString(omexmlstr)
                (__, result) = parse_element(dom)
                logger.debug(result)
                metadata = self.get_metadata(result, 'file', file_id, host)
                logger.debug(metadata)
                # upload metadata
                pyclowder.files.upload_metadata(connector, host, secret_key, file_id, metadata)

            except Exception as e:
                logger.error("Error getting metadata from file", e)
        else:
            logger.error(f"File format not supprted, Supported list:{self.bioformat_extensions}")
        


if __name__ == "__main__":
    javabridge.start_vm(class_path=bioformats.JARS)
    extractor = BioformatExtractor()
    extractor.start()
    javabridge.kill_vm()
