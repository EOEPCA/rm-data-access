import logging

from copy import deepcopy
from datetime import datetime
import json
from typing import Optional
from urllib.parse import urlencode, urljoin, uses_netloc, uses_relative

from lxml import etree
from owslib.iso import MD_Metadata
from owslib.ogcapi.processes import Processes
from pygeometa.schemas.iso19139 import ISO19139OutputSchema
from pygeometa.schemas.iso19139_2 import ISO19139_2OutputSchema
import yaml

LANGUAGE = 'eng'

logger = logging.getLogger(__name__)


class ISOMetadata:
    def __init__(self, base_url: str):
        logger.debug('Adding s3 to urllib supported protocols for urljoin')
        uses_netloc.append('s3')
        uses_relative.append('s3')

        self.base_url = base_url.rstrip('/') + '/'

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

        if 's:releaseNotes' in cwl:
            mcf['dataquality']['lineage']['statement'] = cwl['s:releaseNotes']
            mcf['dataquality']['scope'] = {'level': 'application'}
            mcf['distribution']['releaseNotes'] = {
                'rel': 'related',
                'url': cwl['s:releaseNotes'],
                'type': 'text/html',
                'name': 'releaseNotes',
                'description': 'release notes',
                'function': 'version-history'
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
            'description': wf['doc'],
            'function': 'enclosure'
        }

        mcf['distribution']['http'] = {
            'rel': 'data',
            'url': public_s3_url,
            'type': 'application/x-yaml',
            'name': wf['label'],
            'description': wf['doc'],
            'function': 'enclosure'
        }

        if 's:citation' in cwl:
            mcf['distribution']['citation'] = {
                'rel': 'cite-as',
                'url': cwl['s:citation'],
                'type': 'text/html',
                'name': 'citation',
                'description': 'citation',
                'function': 'cite-as'
            }

        if 's:codeRepository' in cwl:
            mcf['distribution']['codeRepository'] = {
                'rel': 'related',
                'url': cwl['s:codeRepository'],
                'type': 'text/html',
                'name': 'codeRepository',
                'description': 'code repository',
                'function': 'working-copy-of'
            }

        if 's:license' in cwl:
            mcf['distribution']['license'] = {
                'rel': 'license',
                'url': cwl['s:license'],
                'type': 'text/html',
                'name': 'license',
                'description': 'license',
                'function': 'license'
            }

        if 's:logo' in cwl:
            mcf['distribution']['logo'] = {
                'rel': 'icon',
                'url': cwl['s:logo'],
                'type': 'text/html',
                'name': 'logo',
                'description': 'logo',
                'function': 'icon'
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

    def from_stac_item(self, stac_item: str, ows_url: str) -> str:
        mcf = deepcopy(self.mcf)

        si = json.loads(stac_item)
        product_manifest = si['id']

        mcf['metadata']['identifier'] = si['id']
        mcf['metadata']['datestamp'] = si['properties']['datetime']
        mcf['metadata']['hierarchylevel'] = 'dataset'

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
                'rel': 'data',
                'url': urljoin(self.base_url, value['href']),
                'type': value['type'],
                'name': value.get('title'),
                'description': value.get('title'),
                'function': 'download'
            }
            mcf['distribution'][key] = dist

        mcf['distribution'][si['id']] = {
            'rel': 'enclosure',
            'url': self.base_url,
            'type': 'enclosure',
            'name': 'product',
            'description': 'product',
            'function': 'download'
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
            'name': product_manifest,
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
            'name': product_manifest,
            'description': f'WCS URL for {product_manifest}',
        }

        logger.debug(f'MCF: {mcf}')

        iso_os = ISO19139_2OutputSchema()

        return iso_os.write(mcf)

    def from_esa_iso_xml(self, esa_xml: bytes, inspire_xml: bytes,
                         collections: list, ows_url: str, stac_id: str) -> str:

        mcf = deepcopy(self.mcf)

        exml = etree.fromstring(esa_xml)
        ixml = etree.fromstring(inspire_xml)

        product_type = exml.xpath('//PRODUCT_TYPE/text()')[0]

        m = MD_Metadata(ixml)

        product_manifest = exml.xpath('//PRODUCT_URI/text()')[0]
        product_manifest_link = urljoin(self.base_url, product_manifest)

        if stac_id:
            mcf['metadata']['identifier'] = stac_id
        else:
            mcf['metadata']['identifier'] = product_manifest
        mcf['metadata']['hierarchylevel'] = m.hierarchy or 'dataset'
        mcf['metadata']['datestamp'] = exml.xpath('//Product_Info/GENERATION_TIME/text()')[0]

        if product_type in collections:
            mcf['metadata']['parentidentifier'] = product_type

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

        mcf['identification']['title'] = product_manifest
        mcf['identification']['abstract'] = product_manifest

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
            logger.warning(f'unknown product format: {product_format}')
            mime_type = 'NA'
            file_extension = 'NA'

        for image_file in exml.xpath('//Product_Organisation//IMAGE_FILE/text()'):
            dist = {
                'rel': 'enclosure',
                'url': urljoin(product_manifest_link, f'{image_file}.{file_extension}'),
                'type': mime_type,
                'name': 'granule',
                'description': 'granule',
                'function': 'download'
            }
            mcf['distribution'][image_file] = dist

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
            'name': product_manifest,
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
            'name': product_manifest,
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

        mcf['metadata']['identifier'] = ades_url
        mcf['metadata']['hierarchylevel'] = 'application'
        mcf['metadata']['datestamp'] = now

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
                'description': name,
                'function': link.get('rel')
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

    def from_stac_collection(self, stac_collection: str) -> str:
        mcf = deepcopy(self.mcf)

        now = datetime.now().isoformat()

        sc = json.loads(stac_collection)

        mcf['metadata']['identifier'] = sc['id']
        mcf['metadata']['hierarchylevel'] = 'dataset'
        mcf['metadata']['datestamp'] = now

        mcf['identification']['title'] = sc['id']
        mcf['identification']['abstract'] = sc['description']

        mcf['identification']['extents'] = {
            'spatial': [{
                'bbox': sc['extents']['spatial']['bbox'][0],
                'crs': 4326
            }]
        }

        mcf['identification']['keywords']['default'] = {
            'keywords': ['collection'],
            'keywords_type': 'theme'
        }

        for key, value in sc['links'].items():
            dist = {
                'rel': value.get('rel'),
                'url': value.get('href'),
                'type': value.get('type'),
                'name': value.get('title'),
                'description': value.get('title'),
                'function': value.get('rel')
            }
            mcf['distribution'][key] = dist

        logger.debug(f'MCF: {mcf}')

        iso_os = ISO19139_2OutputSchema()

        return iso_os.write(mcf)