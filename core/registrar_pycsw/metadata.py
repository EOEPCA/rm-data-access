import logging

from lxml import etree
from owslib.iso import MD_Metadata
from pygeometa.schemas.iso19139 import ISO19139OutputSchema

LANGUAGE = 'eng'

logger = logging.getLogger(__name__)

mcf = {
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
        'keywords': {}
    },
    'contact': {
      'main': {},
      'distribution': {}
    },
    'distribution': {}
}


def gen_iso_metadata(base_url: str, esa_xml: bytes, inspire_xml: bytes) -> str:
    exml = etree.fromstring(esa_xml)
    ixml = etree.fromstring(inspire_xml)

    m = MD_Metadata(ixml)

    product_manifest = exml.xpath('//PRODUCT_URI/text()')[0]
    product_identifier = product_manifest.replace('.SAFE', '')
    product_manifest_link = f"{base_url}/{product_manifest}"

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

    mcf['identification']['topiccategory'] = [m.identification.topiccategory[0]]
    mcf['identification']['status'] = 'onGoing'
    mcf['identification']['maintenancefrequency'] = 'continual'
    mcf['identification']['accessconstraints'] = m.identification.accessconstraints[0]

    mcf['distribution'][product_manifest] = {
        'url': product_manifest_link,
        'type': 'enclosure',
        'name': product_manifest,
        'description': product_manifest,
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
            'url': f"{product_manifest_link}/{image_file}.{file_extension}",
            'type': mime_type,
            'name': image_file,
            'description': image_file,
            'function': 'download'
        }
        mcf['distribution'][image_file] = dist

    logger.debug("MCF: {}".format(mcf))

    iso_os = ISO19139OutputSchema()

    return iso_os.write(mcf)
