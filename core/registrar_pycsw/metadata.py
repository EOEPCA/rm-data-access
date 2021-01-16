import logging

from copy import deepcopy
import json
from os.path import normpath

from lxml import etree
from owslib.iso import MD_Metadata
from pygeometa.schemas.iso19139_2 import ISO19139_2OutputSchema

LANGUAGE = 'eng'

logger = logging.getLogger(__name__)


class ISOMetadata:
    def __init__(self, base_url: str):

        self.base_url = base_url

        self.mcf = {
            'mcf': {
                'version': '1.0'
            },
            'metadata': {
                'language': LANGUAGE,
                'charset': 'utf8',
                'parentidentifier': 'TBD'
            },
            'spatial': {
                'datatype': 'grid',
                'geomtype': 'solid'
            },
            'identification': {
                'charset': 'utf8',
                'language': 'missing',
                'keywords': {},
                'status': 'onGoing',
                'maintenancefrequency': 'continual'
            },
            'content_info': {
                'type': 'image',
                'dimensions': []
            },
            'contact': {
              'main': {},
              'distribution': {}
            },
            'distribution': {}
        }

    def from_stac_item(self, stac_item: str) -> str:
        mcf = deepcopy(self.mcf)

        si = json.loads(stac_item)

        mcf['metadata']['identifier'] = si['id']
        mcf['metadata']['datestamp'] = si['properties']['datetime']

        mcf['identification']['title'] = si['id']

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': si['bbox'],
                'crs': 4326
            }],
            'temporal': [{
                'instant': si['properties']['datetime']
             }]
        }

        for eo_band in si['properties']['eo:bands']:
            mcf['content_info']['dimensions'].append({
                'name': eo_band['name']
            })

        mcf['identification']['dates'] = {
            'creation': si['properties']['datetime'],
            'publication': si['properties']['datetime']
        }

        mcf['identification']['keywords']['eo:bands'] = {
            'keywords': [x['common_name'] for x in si['properties']['eo:bands']],
            'keywords_type': 'theme'
        }

        mcf['identification']['keywords']['default'] = {
            'keywords': ['processing'],
            'keywords_type': 'theme'
        }

        mcf['acquisition'] = {
            'platforms': [{
                'identifier': si['properties']['eo:platform'],
                'description': si['properties']['eo:platform'],
                'instruments': [{
                    'identifier': si['properties']['eo:instrument'],
                    'type': si['properties']['eo:instrument']
                }]
            }]
        }

        for key, value in si['assets'].items():
            dist = {
                'url': normpath(f"{self.base_url}/{value['href']}"),
                'type': value['type'],
                'name': value['title'],
                'description': value['title'],
                'function': 'download'
            }
            mcf['distribution'][key] = dist

        logger.debug('MCF: {}'.format(mcf))

        iso_os = ISO19139_2OutputSchema()

        return iso_os.write(mcf)

    def from_esa_iso_xml(self, esa_xml: bytes, inspire_xml: bytes) -> str:
        mcf = deepcopy(self.mcf)

        exml = etree.fromstring(esa_xml)
        ixml = etree.fromstring(inspire_xml)

        m = MD_Metadata(ixml)

        product_manifest = exml.xpath('//PRODUCT_URI/text()')[0]
        product_identifier = product_manifest.replace('.SAFE', '')
        product_manifest_link = normpath(
            f'{self.base_url}/{product_manifest}')

        mcf['metadata']['identifier'] = product_identifier
        mcf['metadata']['hierarchylevel'] = m.hierarchy
        mcf['metadata']['datestamp'] = exml.xpath('//Product_Info/GENERATION_TIME/text()')[0]

        gfp = exml.xpath('//Global_Footprint/EXT_POS_LIST/text()')[0].split()

        minx = gfp[1]
        miny = gfp[0]
        maxx = gfp[5]
        maxy = gfp[4]

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': [minx, miny, maxx, maxy],
                'crs': 4326
            }],
            'temporal': [{
                'begin': exml.xpath('//Product_Info/PRODUCT_START_TIME/text()')[0],
                'end': exml.xpath('//Product_Info/PRODUCT_STOP_TIME/text()')[0]
            }]
        }

        mcf['identification']['title'] = product_identifier
        mcf['identification']['abstract'] = product_identifier

        mcf['identification']['dates'] = {
            'creation': mcf['metadata']['datestamp'],
            'publication': mcf['metadata']['datestamp']
        }

        for i, kws in enumerate(m.identification.keywords):
            kw_set = 'kw{}'.format(i)

            mcf['identification']['keywords'][kw_set] = {
                'keywords': kws['keywords']
            }
            mcf['identification']['keywords'][kw_set]['keywords_type'] = kws['type'] or 'theme'

        product_type = f"eo:productType:{exml.xpath('//PRODUCT_TYPE/text()')[0]}"
        orbit_number = f"eo:orbitNumber:{exml.xpath('//SENSING_ORBIT_NUMBER/text()')[0]}"
        orbit_direction = f"eo:orbitDirection:{exml.xpath('//SENSING_ORBIT_DIRECTION/text()')[0]}"
        snow_cover = f"eo:snowCover:{exml.xpath('//SNOW_ICE_PERCENTAGE/text()')[0]}"

        mcf['identification']['keywords']['product'] = {
                'keywords': [
                    product_type,
                    orbit_number,
                    orbit_direction,
                    snow_cover
                ],
                'keywords_type': 'theme'
        }

        mcf['identification']['topiccategory'] = [m.identification.topiccategory[0]]
        mcf['identification']['status'] = 'onGoing'
        mcf['identification']['maintenancefrequency'] = 'continual'
        mcf['identification']['accessconstraints'] = m.identification.accessconstraints[0]

        mcf['content_info']['cloud_cover'] = exml.xpath('//Cloud_Coverage_Assessment/text()')[0]
        mcf['content_info']['processing_level'] = exml.xpath('//PROCESSING_LEVEL/text()')[0]

        for d in exml.xpath('//Spectral_Information_List/Spectral_Information'):
            mcf['content_info']['dimensions'].append({
                'name': d.attrib.get('physicalBand'),
                'units': d.xpath('//CENTRAL')[0].attrib.get('unit'),
                'min': d.xpath('//MIN/text()')[0],
                'max': d.xpath('//MAX/text()')[0]
            })

        mcf['distribution'][product_manifest] = {
            'url': product_manifest_link,
            'type': 'enclosure',
            'name': 'product',
            'description': 'product',
            'function': 'download'
        }

        product_format = exml.xpath('//Granule_List/Granule/@imageFormat')[0]

        if product_format == 'JPEG2000':
            mime_type = 'image/jp2'
            file_extension = 'jp2'
        elif product_format == 'TIFF':
            mime_type = 'image/x.geotiff'
            file_extension = 'tif'
        else:
            logger.warning('unknown product format: {}'.format(product_format))
            mime_type = 'NA'
            file_extension = 'NA'

        for image_file in exml.xpath('//Product_Organisation//IMAGE_FILE/text()'):
            dist = {
                'url': normpath(
                    f'{product_manifest_link}/{image_file}.{file_extension}'),
                'type': mime_type,
                'name': 'granule',
                'description': 'granule',
                'function': 'download'
            }
            mcf['distribution'][image_file] = dist

        mcf['acquisition'] = {
            'platforms': [{
                'identifier': exml.xpath('//SPACECRAFT_NAME/text()')[0],
                'description': exml.xpath('//SPACECRAFT_NAME/text()')[0],
                'instruments': [{
                    'identifier': exml.xpath('//DATATAKE_TYPE/text()')[0],
                    'type': exml.xpath('//PRODUCT_TYPE/text()')[0]
                }]
            }]
        }

        logger.debug('MCF: {}'.format(mcf))

        iso_os = ISO19139_2OutputSchema()

        return iso_os.write(mcf)
