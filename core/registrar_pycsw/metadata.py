import logging

from copy import deepcopy
from datetime import datetime
import json
import yaml
import re
from typing import Optional
from urllib.parse import urlencode, urljoin, uses_netloc, uses_relative

from lxml import etree
from owslib.iso import MD_Metadata
from owslib.ogcapi.processes import Processes
from pygeometa.schemas.iso19139 import ISO19139OutputSchema
from pygeometa.schemas.iso19139_2 import ISO19139_2OutputSchema

LANGUAGE = 'eng'

logger = logging.getLogger(__name__)


if 's3' not in uses_netloc:
    uses_netloc.append('s3')
if 's3' not in uses_relative:
    uses_relative.append('s3')


class ISOMetadata:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/') + '/'

        self.mcf = {
            'mcf': {
                'version': '1.0'
            },
            'metadata': {
                'language': LANGUAGE,
                'charset': 'utf8'
            },
            'spatial': {
                'datatype': 'grid',
                'geomtype': 'solid'
            },
            'identification': {
                'charset': 'utf8',
                'language': 'missing',
                'keywords': {},
                'dates': {},
                'status': 'onGoing',
                'maintenancefrequency': 'continual'
            },
            'content_info': {
                'type': 'image',
                'dimensions': []
            },
            'contact': {
              'pointOfContact': {},
              'distributor': {},
              'author': {}
            },
            'distribution': {},
            'dataquality': {
                'lineage': {}
            }
        }

    def from_cwl(self, cwl_item: str, public_s3_url: str,
                 parent_identifier: Optional[str] = None) -> str:
        mcf = deepcopy(self.mcf)

        now = datetime.now().isoformat()

        cwl = yaml.load(cwl_item, Loader=yaml.SafeLoader)

        wf = list(filter(lambda x: x['class'] == 'Workflow', cwl['$graph']))[0]

        mcf['metadata']['identifier'] = wf['id']
        mcf['metadata']['hierarchylevel'] = 'application'
        mcf['metadata']['datestamp'] = now
        mcf['identification']['title'] = wf['label']
        mcf['identification']['abstract'] = wf['doc']

        mcf['identification']['keywords']['default'] = {
            'keywords': [f'softwareVersion:{cwl["s:softwareVersion"]}', 'application', 'CWL'],
            'keywords_type': 'theme'
        }

        if 's:keywords' in cwl:
            mcf['identification']['keywords']['default']['keywords'].extend(
                cwl['s:keywords'].split(',')
            )

        mcf['dataquality']['scope'] = {'level': 'application'}

        if 's:releaseNotes' in cwl:
            mcf['dataquality']['lineage']['statement'] = cwl['s:releaseNotes']
            mcf['distribution']['releaseNotes'] = {
                'rel': 'related',
                'url': cwl['s:releaseNotes'],
                'type': 'text/html',
                'name': 'releaseNotes',
                'description': 'release notes'
            }

        if 's:version' in cwl:
            mcf['identification']['edition'] = cwl['s:version']

        if 's:author' in cwl:
            mcf['contact']['author'] = {
                'individualname': cwl['s:author'][0]['s:name'],
                'organization': cwl['s:author'][0]['s:affiliation'],
                'email': cwl['s:author'][0]['s:email'],
            }

        if 's:contributor' in cwl:
            mcf['contact']['pointOfContact'] = {
                'individualname': cwl['s:contributor'][0]['s:name'],
                'organization': cwl['s:contributor'][0]['s:affiliation'],
                'email': cwl['s:contributor'][0]['s:email'],
            }

        if 's:dateCreated' in cwl:
            mcf['identification']['dates'] = {
                'creation': cwl['s:dateCreated']
            }

        mcf['distribution']['cwl'] = {
            'rel': 'manifest',
            'url': self.base_url.rstrip('/'),
            'type': 'application/x-yaml',
            'name': wf['label'],
            'description': wf['doc']
        }

        mcf['distribution']['http'] = {
            'rel': 'data',
            'url': public_s3_url,
            'type': 'application/x-yaml',
            'name': wf['label'],
            'description': wf['doc']
        }

        if 's:citation' in cwl:
            mcf['distribution']['citation'] = {
                'rel': 'cite-as',
                'url': cwl['s:citation'],
                'type': 'text/html',
                'name': 'citation',
                'description': 'citation'
            }

        if 's:codeRepository' in cwl:
            mcf['distribution']['codeRepository'] = {
                'rel': 'working-copy-of',
                'url': cwl['s:codeRepository'],
                'type': 'text/html',
                'name': 'codeRepository',
                'description': 'code repository'
            }

        if 's:license' in cwl:
            mcf['distribution']['license'] = {
                'rel': 'license',
                'url': cwl['s:license'],
                'type': 'text/html',
                'name': 'license',
                'description': 'license'
            }

        if 's:logo' in cwl:
            mcf['distribution']['logo'] = {
                'rel': 'icon',
                'url': cwl['s:logo'],
                'type': 'text/html',
                'name': 'logo',
                'description': 'logo'
            }

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': [-180, -90, 180, 90],
                'crs': 4326
            }],
        }

        if parent_identifier is not None:
            mcf['metadata']['parentidentifier'] = parent_identifier

        logger.info(f'MCF: {mcf}')

        iso_os = ISO19139OutputSchema()

        return iso_os.write(mcf)

    def from_stac_item(self, stac_item: str, collections: list, ows_url: str) -> str:
        mcf = deepcopy(self.mcf)

        si = json.loads(stac_item)
        product_manifest = si['id']

        mcf['metadata']['identifier'] = si['id']
        mcf['metadata']['datestamp'] = si['properties']['datetime']
        mcf['metadata']['hierarchylevel'] = 'dataset'

        mcf['identification']['title'] = si.get('title', si.get('id'))

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': si['bbox'],
                'crs': 4326
            }],
            'temporal': [{
                'instant': si['properties']['datetime']
             }]
        }

        if 'eo:bands' in si['properties']:
            bands = si['properties']['eo:bands']
        else:
            bands = []
            for asset in si['assets'].values():
                if 'eo:bands' in asset:
                    bands.extend(asset['eo:bands'])

        for eo_band in bands:
            mcf['content_info']['dimensions'].append({
                'name': eo_band['name']
            })

        mcf['identification']['dates'] = {
            'creation': si['properties']['datetime'],
            'publication': si['properties']['datetime']
        }

        mcf['identification']['keywords']['eo:bands'] = {
            'keywords': [x['common_name'] for x in bands],
            'keywords_type': 'theme'
        }

        mcf['identification']['keywords']['default'] = {
            'keywords': ['processing'],
            'keywords_type': 'theme'
        }

        properties = si['properties']
        platform = properties.get('platform') or properties.get('eo:platform')
        instrument = properties.get('instrument') or properties.get('eo:instrument')  # noqa
        collection = properties.get('collection', '')

        if collection in collections:
            mcf['metadata']['parentidentifier'] = collection

        mcf['dataquality'] = {
            'scope': {
                'level': 'dataset'
            },
            'lineage': {
                'statement': f"Processed from platform {platform}, instrument {instrument}"  # noqa
            }
        }

        mcf['acquisition'] = {
            'platforms': [{
                'identifier': platform,
                'description': platform,
                'instruments': [{
                    'identifier': instrument,
                    'type': instrument,
                }]
            }]
        }

        for key, value in si['assets'].items():
            dist = {
                'rel': 'enclosure',
                'url': urljoin(self.base_url, value['href']),
                'type': value.get('type'),
                'name': key,
                'description': value.get('title', key)
            }
            mcf['distribution'][key] = dist

        mcf['distribution'][si['id']] = {
            'rel': 'alternate',
            'url': self.base_url,
            'type': 'application/octet-stream',
            'name': 'product',
            'description': 'product'
        }

        logger.debug('Adding WMS/WCS links')
        wms_link_params = {
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wms',
            'service': 'WMS',
            'version': '1.3.0',
            'request': 'GetCapabilities',
            'cql': f'identifier="{product_manifest}"'
        }

        mcf['distribution']['wms_link'] = {
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wms',
            'url': f'{ows_url}?{urlencode(wms_link_params)}',
            'type': 'OGC:WMS',
            'name': 'OGC WMS',
            'description': f'WMS URL for {product_manifest}',
        }

        wcs_link_params = {
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wcs',
            'service': 'WCS',
            'version': '2.0.1',
            'request': 'DescribeEOCoverageSet',
            'eoid': product_manifest
        }

        mcf['distribution']['wcs_link'] = {
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wcs',
            'url': f'{ows_url}?{urlencode(wcs_link_params)}',
            'type': 'OGC:WCS',
            'name': 'OGC WCS',
            'description': f'WCS URL for {product_manifest}',
        }

        logger.debug(f'MCF: {mcf}')

        iso_os = ISO19139_2OutputSchema()

        return iso_os.write(mcf)

    def from_esa_iso_xml(self, esa_xml: bytes, inspire_xml: bytes, stac_item: str,
                         collections: list, ows_url: str) -> str:

        mcf = deepcopy(self.mcf)
        si = json.loads(stac_item)

        exml = etree.fromstring(esa_xml)
        ixml = etree.fromstring(inspire_xml)

        product_type = exml.xpath('//PRODUCT_TYPE/text()')[0]

        m = MD_Metadata(ixml)

        product_manifest = exml.xpath('//PRODUCT_URI/text()')[0]
        # product_manifest_link = urljoin(self.base_url, product_manifest)

        if si.get('id') is not None:
            mcf['metadata']['identifier'] = si['id']
        else:
            mcf['metadata']['identifier'] = product_manifest
        mcf['metadata']['hierarchylevel'] = m.hierarchy or 'dataset'
        mcf['metadata']['datestamp'] = exml.xpath('//Product_Info/GENERATION_TIME/text()')[0]

        if product_type in collections:
            mcf['metadata']['parentidentifier'] = product_type

        gfp = exml.xpath('//Global_Footprint/EXT_POS_LIST/text()')[0].split()

        xlist = gfp[1::2]
        ylist = gfp[::2]

        minx = min(xlist)
        miny = min(ylist)
        maxx = max(xlist)
        maxy = max(ylist)

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

        mcf['identification']['title'] = product_manifest
        mcf['identification']['abstract'] = product_manifest
        mcf.pop('dataquality', None)

        mcf['identification']['dates'] = {
            'creation': mcf['metadata']['datestamp'],
            'publication': mcf['metadata']['datestamp']
        }

        for i, kws in enumerate(m.identification.keywords):
            kw_set = f'kw{i}'

            mcf['identification']['keywords'][kw_set] = {
                'keywords': kws['keywords']
            }
            mcf['identification']['keywords'][kw_set]['keywords_type'] = kws['type'] or 'theme'

        keyword_xpaths = {
            'eo:productType': '//PRODUCT_TYPE/text()',
            'eo:orbitNumber': '//SENSING_ORBIT_NUMBER/text()',
            'eo:orbitDirection': '//SENSING_ORBIT_DIRECTION/text()',
            'eo:snowCover': '//SNOW_ICE_PERCENTAGE/text()'
        }

        mcf['identification']['keywords']['product'] = {
            'keywords': [],
            'keywords_type': 'theme'
        }

        for key, value in keyword_xpaths.items():
            if len(exml.xpath(value)) > 0:
                keyword = value[0]
                mcf['identification']['keywords']['product']['keywords'].append(
                    f"{key}:{keyword}")

        mcf['identification']['topiccategory'] = [m.identification.topiccategory[0]]
        mcf['identification']['status'] = 'onGoing'
        mcf['identification']['maintenancefrequency'] = 'continual'
        mcf['identification']['accessconstraints'] = m.identification.accessconstraints[0]

        if len(exml.xpath('//Cloud_Coverage_Assessment/text()')) > 0:
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
            'rel': 'alternate',
            'url': self.base_url,
            'type': 'application/octet-stream',
            'name': 'product',
            'description': 'product'
        }

        product_format = exml.xpath('//Granule_List/Granule/@imageFormat')[0]

        if product_format == 'JPEG2000':
            mime_type = 'image/jp2'
            file_extension = 'jp2'
        elif product_format == 'TIFF':
            mime_type = 'image/x.geotiff'
            file_extension = 'tif'
        else:
            logger.warning(f'unknown product format: {product_format}')
            mime_type = 'NA'
            file_extension = 'NA'

        # for image_file in exml.xpath('//Product_Organisation//IMAGE_FILE/text()'):
        #     dist = {
        #         'rel': 'enclosure',
        #         'url': urljoin(product_manifest_link, f'{image_file}.{file_extension}'),
        #         'type': mime_type,
        #         'name': 'granule',
        #         'description': 'granule'
        #     }
        #     mcf['distribution'][image_file] = dist

        for key, value in si['assets'].items():
            dist = {
                'rel': 'enclosure',
                'url': urljoin(self.base_url, value['href']),
                'type': value.get('type'),
                'name': key,
                'description': value.get('title', key)
            }
            mcf['distribution'][key] = dist

        logger.debug('Adding WMS/WCS links')
        wms_link_params = {
            'service': 'WMS',
            'version': '1.3.0',
            'request': 'GetCapabilities',
            'cql': f'identifier="{product_manifest}"'
        }

        mcf['distribution']['wms_link'] = {
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wms',
            'url': f'{ows_url}?{urlencode(wms_link_params)}',
            'type': 'OGC:WMS',
            'name': 'OGC WMS',
            'description': f'WMS URL for {product_manifest}',
        }

        wcs_link_params = {
            'service': 'WCS',
            'version': '2.0.1',
            'request': 'DescribeEOCoverageSet',
            'eoid': product_manifest
        }

        mcf['distribution']['wcs_link'] = {
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wcs',
            'url': f'{ows_url}?{urlencode(wcs_link_params)}',
            'type': 'OGC:WCS',
            'name': 'OGC WCS',
            'description': f'WCS URL for {product_manifest}',
        }

        mcf['acquisition'] = {
            'platforms': [{
                'identifier': exml.xpath('//SPACECRAFT_NAME/text()')[0],
                'description': exml.xpath('//SPACECRAFT_NAME/text()')[0],
                'instruments': [{
                    'identifier': exml.xpath('//DATATAKE_TYPE/text()')[0],
                    'type': product_type
                }]
            }]
        }

        logger.debug(f'MCF: {mcf}')

        iso_os = ISO19139_2OutputSchema()

        return iso_os.write(mcf)

    def from_ades(self, ades_url: str,
                  parent_identifier: Optional[str] = None) -> str:
        mcf = deepcopy(self.mcf)

        now = datetime.now().isoformat()

        ades = Processes(ades_url)

        mcf['metadata']['identifier'] = re.sub('[^a-zA-Z0-9 \n]', '-', ades_url)
        mcf['metadata']['hierarchylevel'] = 'service'
        mcf['metadata']['datestamp'] = now
        mcf.pop('dataquality', None)

        mcf['identification']['title'] = ades.response.get('title')
        mcf['identification']['abstract'] = ades.response.get('description')
        mcf['identification']['dates'] = {
                'creation': now
            }

        mcf['identification']['keywords']['default'] = {
            'keywords': ['application', 'ADES', 'OGC API - Processes', 'service', 'process'],
            'keywords_type': 'theme'
        }

        mcf['distribution']['http'] = {
            'rel': 'service',
            'url': ades_url,
            'type': 'application/json',
            'name': ades.response.get('title'),
            'description': ades.response.get('description'),
            'function': 'service'
        }

        for link in ades.links:
            name = link.get('title')
            mcf['distribution'][name] = {
                'rel': link.get('rel'),
                'url': link.get('href'),
                'type': link.get('type'),
                'name': name,
                'description': name
            }

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': [-180, -90, 180, 90],
                'crs': 4326
            }],
        }

        if parent_identifier is not None:
            mcf['metadata']['parentidentifier'] = parent_identifier

        logger.info(f'MCF: {mcf}')

        iso_os = ISO19139OutputSchema()

        return iso_os.write(mcf)

    def from_oaproc(self, oaproc_url: str,
                    parent_identifier: Optional[str] = None,
                    registration_type: Optional[str] = None) -> str:
        mcf = deepcopy(self.mcf)

        now = datetime.now().isoformat()

        oaproc = Processes(oaproc_url)

        oaproc_id = re.sub('[^a-zA-Z0-9 \n]', '-', oaproc_url)
        mcf['metadata']['identifier'] = oaproc_id
        mcf['metadata']['hierarchylevel'] = 'service'
        mcf['metadata']['datestamp'] = now
        mcf.pop('dataquality', None)

        mcf['identification']['title'] = oaproc.response.get('title')
        mcf['identification']['abstract'] = oaproc.response.get('description')
        mcf['identification']['dates'] = {
            'creation': now
        }

        kw = ['OGC API - Processes', 'service', 'application', 'process']
        if registration_type == 'ades':
            kw.append('ADES')

        mcf['identification']['keywords']['default'] = {
            'keywords': kw,
            'keywords_type': 'theme'
        }

        mcf['distribution']['http'] = {
            'rel': 'service',
            'url': oaproc_url,
            'type': 'application/json',
            'name': oaproc.response.get('title'),
            'description': oaproc.response.get('description'),
            'function': 'service'
        }

        for link in oaproc.links:
            name = link.get('title')
            mcf['distribution'][name] = {
                'rel': link.get('rel'),
                'url': link.get('href'),
                'type': link.get('type'),
                'name': name,
                'description': name
            }

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': [-180, -90, 180, 90],
                'crs': 4326
            }],
        }

        if parent_identifier is not None:
            mcf['metadata']['parentidentifier'] = parent_identifier

        logger.info(f'OGC API - Processes MCF: {mcf}')

        iso_os = ISO19139OutputSchema()

        records = []
        records.append(iso_os.write(mcf))

        if registration_type != 'ades':
            for process in oaproc.processes():
                mcf = {}
                mcf = deepcopy(self.mcf)
                mcf['metadata']['identifier'] = oaproc_id + '-' + process['id']
                mcf['metadata']['hierarchylevel'] = 'service'
                mcf['metadata']['datestamp'] = now
                mcf.pop('dataquality', None)

                mcf['identification']['title'] = process['title']
                mcf['identification']['abstract'] = process['description']
                mcf['identification']['dates'] = {
                    'creation': now
                }

                mcf['identification']['keywords']['service'] = {
                    'keywords': ['OGC API - Processes', 'service', 'application', 'process', 'OAProc'],
                    'keywords_type': 'theme'
                }

                if 'keywords' in process:
                    mcf['identification']['keywords']['default'] = {
                        'keywords': process['keywords'],
                        'keywords_type': 'theme'
                    }

                mcf['distribution']['http'] = {
                    'rel': 'service',
                    'url': oaproc_url,
                    'type': 'application/json',
                    'name': oaproc.response['title'],
                    'description': oaproc.response['description'],
                    'function': 'service'
                }

                for link in process['links']:
                    name = link.get('title')
                    mcf['distribution'][name] = {
                        'rel': link.get('rel'),
                        'url': link.get('href'),
                        'type': link.get('type'),
                        'name': name,
                        'description': name
                    }

                mcf['identification']['extents'] = {
                    'spatial': [{
                        'bbox': [-180, -90, 180, 90],
                        'crs': 4326
                    }],
                }

                mcf['metadata']['parentidentifier'] = oaproc_id

                logger.info(f'Process MCF: {mcf}')

                iso_os = ISO19139OutputSchema()

                records.append(iso_os.write(mcf))

        return records

    def from_oarec(self, landing_page: dict, is_stac_api: bool = False) -> str:
        mcf = deepcopy(self.mcf)

        now = datetime.now().isoformat()

        oarec_id = re.sub('[^a-zA-Z0-9 \n]', '-', self.base_url)
        mcf['metadata']['identifier'] = oarec_id
        mcf['metadata']['hierarchylevel'] = 'service'
        mcf['metadata']['datestamp'] = now
        mcf.pop('dataquality', None)

        mcf['identification']['title'] = landing_page.get('title')
        mcf['identification']['abstract'] = landing_page.get('description')
        mcf['identification']['dates'] = {
            'creation': now
        }

        kw = ['service', 'application', 'metadata']

        if is_stac_api:
            kw.append('STAC API')
        else:
            kw.append('OGC API - Records')

        mcf['identification']['keywords']['default'] = {
            'keywords': kw,
            'keywords_type': 'theme'
        }

        mcf['distribution']['http'] = {
            'rel': 'service',
            'url': self.base_url,
            'type': 'application/json',
            'name': landing_page.get('title'),
            'description': landing_page.get('description'),
            'function': 'service'
        }

        for link in landing_page['links']:
            name = link.get('title')
            mcf['distribution'][name] = {
                'rel': link.get('rel'),
                'url': link.get('href'),
                'type': link.get('type'),
                'name': name,
                'description': name
            }

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': [-180, -90, 180, 90],
                'crs': 4326
            }],
        }

        logger.info(f'MCF: {mcf}')

        iso_os = ISO19139OutputSchema()

        return iso_os.write(mcf)

    def from_csw(self, capabilities) -> str:
        mcf = deepcopy(self.mcf)

        now = datetime.now().isoformat()

        csw_id = re.sub('[^a-zA-Z0-9 \n]', '-', self.base_url)
        mcf['metadata']['identifier'] = csw_id
        mcf['metadata']['hierarchylevel'] = 'service'
        mcf['metadata']['datestamp'] = now
        mcf.pop('dataquality', None)

        mcf['identification']['title'] = capabilities.identification.title
        mcf['identification']['abstract'] = capabilities.identification.abstract
        mcf['identification']['dates'] = {
            'creation': now
        }

        kw = ['CSW', 'service', 'application', 'metadata']

        mcf['identification']['keywords']['default'] = {
            'keywords': kw,
            'keywords_type': 'theme'
        }

        mcf['distribution']['http'] = {
            'rel': 'service',
            'url': self.base_url,
            'type': 'application/xml',
            'name': capabilities.identification.title,
            'description': capabilities.identification.abstract,
            'function': 'service'
        }

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': [-180, -90, 180, 90],
                'crs': 4326
            }],
        }

        logger.info(f'MCF: {mcf}')

        iso_os = ISO19139OutputSchema()

        return iso_os.write(mcf)

    def from_stac_collection(self, stac_collection: dict) -> str:
        mcf = deepcopy(self.mcf)

        now = datetime.now().isoformat()

        sc = stac_collection

        mcf['metadata']['identifier'] = sc['id']
        mcf['metadata']['hierarchylevel'] = 'dataset'
        mcf['metadata']['datestamp'] = now
        mcf.pop('dataquality', None)

        mcf['identification']['title'] = sc.get('title', sc.get('id'))
        mcf['identification']['abstract'] = sc['description']
        mcf['identification']['dates'] = {
            'creation': now
        }

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': sc['extent']['spatial']['bbox'][0],
                'crs': 4326
            }]
        }

        mcf['identification']['keywords']['default'] = {
            'keywords': ['collection'],
            'keywords_type': 'theme'
        }

        for value in sc['links']:
            # TODO: find better solution! Some rels are not unique.
            key = value['rel']
            dist = {
                'rel': value.get('rel'),
                'url': value.get('href'),
                'type': value.get('type'),
                'name': value.get('title'),
                'description': value.get('title')
            }
            mcf['distribution'][key] = dist

        logger.debug(f'MCF: {mcf}')

        iso_os = ISO19139OutputSchema()

        return iso_os.write(mcf)


class STACMetadata:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/') + '/'

    def from_stac_item(self, stac_item: str, ows_url: str) -> str:

        si = json.loads(stac_item)
        product_manifest = si['id']

        si['links'].append({
            'rel': 'alternate',
            'href': self.base_url,
            'type': 'application/octet-stream',
            'name': 'product',
            'description': 'product'
        })

        logger.debug('Adding WMS/WCS links')
        wms_link_params = {
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wms',
            'service': 'WMS',
            'version': '1.3.0',
            'request': 'GetCapabilities',
            'cql': f'identifier="{product_manifest}"'
        }

        si['links'].append({
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wms',
            'href': f'{ows_url}?{urlencode(wms_link_params)}',
            'type': 'OGC:WMS',
            'name': 'OGC WMS',
            'description': f'WMS URL for {product_manifest}',
        })

        wcs_link_params = {
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wcs',
            'service': 'WCS',
            'version': '2.0.1',
            'request': 'DescribeEOCoverageSet',
            'eoid': product_manifest
        }

        si['links'].append({
            'rel': 'http://www.opengis.net/def/serviceType/ogc/wcs',
            'href': f'{ows_url}?{urlencode(wcs_link_params)}',
            'type': 'OGC:WCS',
            'name': 'OGC WCS',
            'description': f'WCS URL for {product_manifest}',
        })

        logger.debug(f'STAC Item: {si}')

        return json.dumps(si)

    def from_stac_collection(self, stac_collection: dict) -> str:

        sc = stac_collection

        # TODO: Fix links with self.base_url?

        logger.debug(f'STAC Collection: {sc}')

        return json.dumps(sc)
