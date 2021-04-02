import io
import os
import unittest

from lxml import etree

from registrar_pycsw.metadata import ISOMetadata

THISDIR = os.path.dirname(os.path.realpath(__file__))


def get_abspath(filepath):
    return os.path.join(THISDIR, filepath)


def read(filename, encoding='utf-8'):
    """read file contents"""
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with io.open(full_path, 'rb') as fh:
        contents = fh.read().strip()
    return contents


class ISOMetadataTest(unittest.TestCase):
    def setUp(self):
        self.namespaces = {
            'gco': 'http://www.isotc211.org/2005/gco',
            'gmd': 'http://www.isotc211.org/2005/gmd',
            'gmi': 'http://www.isotc211.org/2005/gmi',
            'gml': 'http://www.opengis.net/gml'
        }

    def tearDown(self):
        pass

    def test_from_cwl(self):
        m = ISOMetadata('https://example.org')
        iso = m.from_cwl(read('data/app-s-expression.dev.0.0.2.cwl'))

        self.assertIsInstance(iso, str)

        e = etree.fromstring(iso)
        identifier = e.xpath('//gmd:fileIdentifier/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(identifier, 's-expression')

        title = e.xpath('//gmd:identificationInfo//gmd:title/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(title, 's expressions')

        abstract = e.xpath('//gmd:identificationInfo//gmd:abstract/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(abstract, 'Applies s expressions to EO acquisitions')

        hierarchy_level = e.xpath('//gmd:hierarchyLevel/gmd:MD_ScopeCode/text()', namespaces=self.namespaces)[0]
        self.assertEqual(hierarchy_level, 'application')

        software_version = e.xpath('//gmd:keyword/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(software_version, 'softwareVersion:0.0.2')

        link = e.xpath('//gmd:distributionInfo//gmd:transferOptions//gmd:onLine/gmd:CI_OnlineResource', namespaces=self.namespaces)[0]
        url = link.xpath('gmd:linkage/gmd:URL/text()', namespaces=self.namespaces)[0]
        self.assertEqual(url, 'https://example.org/')

    def test_from_esa_iso_xml(self):
        m = ISOMetadata('https://example.org')
        iso = m.from_esa_iso_xml(
            read('data/MTD_MSIL2A.xml'),
            read('data/INSPIRE.xml'),
            ['S2MSI2A'], 'https://example.org'
        )

        self.assertIsInstance(iso, str)

        e = etree.fromstring(iso)
        identifier = e.xpath('//gmd:fileIdentifier/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(identifier, 'S2B_MSIL2A_20200902T090559_N0214_R050_T34SFF_20200902T113910.SAFE')

        title = e.xpath('//gmd:identificationInfo//gmd:title/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(title, 'S2B_MSIL2A_20200902T090559_N0214_R050_T34SFF_20200902T113910.SAFE')

        abstract = e.xpath('//gmd:identificationInfo//gmd:abstract/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(abstract, 'S2B_MSIL2A_20200902T090559_N0214_R050_T34SFF_20200902T113910.SAFE')

        hierarchy_level = e.xpath('//gmd:hierarchyLevel/gmd:MD_ScopeCode/text()', namespaces=self.namespaces)[0]
        self.assertEqual(hierarchy_level, 'dataset')

        parent_identifier = e.xpath('//gmd:parentIdentifier/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(parent_identifier, 'S2MSI2A')

        keywords = e.xpath('//gmd:keyword/gco:CharacterString/text()', namespaces=self.namespaces)
        self.assertEqual(len(keywords), 9)

        expected_keywords = [
            'data set series',
            'Geographical names',
            'Land cover',
            'Orthoimagery',
            'processing',
            'eo:orbitNumber:/',
            'eo:orbitDirection:/',
            'eo:productType:/',
            'eo:snowCover:/'
        ]

        self.assertEqual(sorted(keywords), sorted(expected_keywords))

        bbox = e.xpath('//gmd:extent//gmd:geographicElement//gco:Decimal/text()', namespaces=self.namespaces)
        self.assertEqual(len(bbox), 4)
        self.assertEqual(bbox, ['22.116947357483525', '22.189438433804188', '36.51756985836932', '36.77470089136385'])

        temporal_begin = e.xpath('//gmd:extent//gmd:temporalElement//gml:beginPosition/text()', namespaces=self.namespaces)[0]
        temporal_end = e.xpath('//gmd:extent//gmd:temporalElement//gml:endPosition/text()', namespaces=self.namespaces)[0]
        self.assertEqual(temporal_begin, temporal_end)
        self.assertEqual(temporal_begin, '2020-09-02T09:05:59.024Z')
        self.assertEqual(temporal_end, '2020-09-02T09:05:59.024Z')

        bands = e.xpath('//gmd:contentInfo//gmd:dimension', namespaces=self.namespaces)
        self.assertEqual(len(bands), 13)

        bands = e.xpath('//gmd:contentInfo//gmd:MD_Band/@id', namespaces=self.namespaces)
        self.assertEqual(len(bands), 13)
        self.assertEqual(bands, ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B10', 'B11', 'B12'])

        band_1_max, band_1_min = e.xpath('//gmd:contentInfo//gmd:MD_Band//gco:Real/text()', namespaces=self.namespaces)[0:2]
        self.assertTrue(band_1_max > band_1_min)

        urls = e.xpath('//gmd:distributionInfo//gmd:transferOptions//gmd:onLine//gmd:URL/text()', namespaces=self.namespaces)
        self.assertEqual(len(urls), 38)

        platform = e.xpath('//gmi:acquisitionInformation//gmi:MI_Platform/gmi:identifier/text()', namespaces=self.namespaces)[0]
        self.assertEqual(platform, 'Sentinel-2B')

        instrument = e.xpath('//gmi:acquisitionInformation//gmi:MI_Platform//gmi:MI_Instrument/gmi:identifier/text()', namespaces=self.namespaces)[0]
        self.assertEqual(instrument, 'INS-NOBS')

        instrument_type = e.xpath('//gmi:acquisitionInformation//gmi:MI_Platform//gmi:MI_Instrument/gmi:type/text()', namespaces=self.namespaces)[0]
        self.assertEqual(instrument_type, 'S2MSI2A')

    def test_from_stac_item(self):
        m = ISOMetadata('https://example.org')
        iso = m.from_stac_item(read('data/INDEX_S2A_MSIL2A_20191216T004701_N0213_R102_T53HPA_20191216T024808.json'))

        self.assertIsInstance(iso, str)

        e = etree.fromstring(iso)
        identifier = e.xpath('//gmd:fileIdentifier/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(identifier, 'INDEX_S2A_MSIL2A_20191216T004701_N0213_R102_T53HPA_20191216T024808')

        title = e.xpath('//gmd:identificationInfo//gmd:title/gco:CharacterString/text()', namespaces=self.namespaces)[0]
        self.assertEqual(title, 'INDEX_S2A_MSIL2A_20191216T004701_N0213_R102_T53HPA_20191216T024808')

        hierarchy_level = e.xpath('//gmd:hierarchyLevel/gmd:MD_ScopeCode/text()', namespaces=self.namespaces)[0]
        self.assertEqual(hierarchy_level, 'dataset')

        keywords = e.xpath('//gmd:keyword/gco:CharacterString/text()', namespaces=self.namespaces)
        self.assertEqual(len(keywords), 4)
        self.assertEqual(sorted(keywords), ['nbr', 'ndvi', 'ndwi', 'processing'])

        bbox = e.xpath('//gmd:extent//gmd:geographicElement//gco:Decimal/text()', namespaces=self.namespaces)
        self.assertEqual(len(bbox), 4)
        self.assertEqual(bbox, ['136.099040812374', '137.333826362695', '-36.227897298303', '-35.2211228310596'])

        bands = e.xpath('//gmd:contentInfo//gmd:dimension', namespaces=self.namespaces)
        self.assertEqual(len(bands), 3)

        bands = e.xpath('//gmd:contentInfo//gmd:MD_Band/@id', namespaces=self.namespaces)
        self.assertEqual(len(bands), 3)
        self.assertEqual(bands, ['NBR', 'NDVI', 'NDWI'])

        urls = e.xpath('//gmd:distributionInfo//gmd:transferOptions//gmd:onLine//gmd:URL/text()', namespaces=self.namespaces)
        self.assertEqual(len(urls), 4)

        expected_urls = [
            'https://example.org/NBR_S2A_MSIL2A_20191216T004701_N0213_R102_T53HPA_20191216T024808.tif',
            'https://example.org/NDVI_S2A_MSIL2A_20191216T004701_N0213_R102_T53HPA_20191216T024808.tif',
            'https://example.org/NDWI_S2A_MSIL2A_20191216T004701_N0213_R102_T53HPA_20191216T024808.tif',
            'https://example.org/'
        ]

        self.assertEqual(urls, expected_urls)

        platform = e.xpath('//gmi:acquisitionInformation//gmi:MI_Platform/gmi:identifier/text()', namespaces=self.namespaces)[0]
        self.assertEqual(platform, 'S2A')

        instrument = e.xpath('//gmi:acquisitionInformation//gmi:MI_Platform//gmi:MI_Instrument/gmi:identifier/text()', namespaces=self.namespaces)[0]
        self.assertEqual(instrument, 'S2MSI')

        instrument_type = e.xpath('//gmi:acquisitionInformation//gmi:MI_Platform//gmi:MI_Instrument/gmi:type/text()', namespaces=self.namespaces)[0]
        self.assertEqual(instrument_type, 'S2MSI')


if __name__ == '__main__':
    unittest.main()
