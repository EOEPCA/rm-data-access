import os
import logging
from typing import Optional
import json
from urllib.parse import urlparse, urljoin, urlunparse
import requests

from lxml import etree
from owslib.csw import CatalogueServiceWeb
from owslib.ogcapi.records import Records
from owslib.opensearch import OpenSearch
from pycsw.core import metadata, repository, util
import pycsw.core.admin
import pycsw.core.config
from pygeometa.core import read_mcf
from pygeometa.schemas.iso19139 import ISO19139OutputSchema
from pystac import Item, Collection
from pystac_client import Client
from registrar.abc import Backend
from registrar.source import Source
from requests.exceptions import JSONDecodeError

from .metadata import ISOMetadata, STACMetadata

logger = logging.getLogger(__name__)

THISDIR = os.path.dirname(__file__)

COLLECTION_LEVEL_METADATA = f'{THISDIR}/resources'


def href_to_path(href):
    """ Gets the path component of a URL
    """
    parsed = urlparse(href)
    return f'{parsed.netloc}{parsed.path}'


class PycswMixIn:
    """ Helper MixIn, to add some common functions when dealing with PyCSW
    """
    def __init__(self, repository_database_uri, ows_url: str = '',
                 public_s3_url: str = ''):
        self.collections = []
        self.ows_url = ows_url
        self.public_s3_url = public_s3_url

        logger.debug('Setting up static context')
        self.context = pycsw.core.config.StaticContext()

        logger.debug('Initializing pycsw repository')
        self.repo = repository.Repository(repository_database_uri,
                                          self.context, table='records')
        logger.debug('Loading collection level metadata identifiers')
        for clm in os.listdir(COLLECTION_LEVEL_METADATA):
            self.collections.append(os.path.splitext(clm)[0])

    def load_collection_level_metadata(self):
        logger.debug('Loading collection level metadata')
        for clm in os.listdir(COLLECTION_LEVEL_METADATA):
            logger.debug(f'collection metadata file: {clm}')
            clm_ = os.path.join(COLLECTION_LEVEL_METADATA, clm)
            clm_mcf = read_mcf(clm_)
            clm_iso = ISO19139OutputSchema().write(clm_mcf)
            logger.debug(f'Upserting metadata: {clm_}')
            self._parse_and_upsert_metadata(clm_iso)

    def _parse_and_upsert_metadata(self, md: str):
        logger.debug('Parsing metadata')
        try:
            metadata_record = json.loads(md)
            metadata_format = 'json'
        except json.decoder.JSONDecodeError:
            try:
                metadata_record = etree.fromstring(md)
            except:
                metadata_record = etree.fromstring(bytes(md, encoding='utf-8'))
            metadata_format = 'xml'
        except Exception as err:
            logger.error(f'Metadata parsing failed: {err}')
            raise

        logger.debug('Processing metadata')
        try:
            record = metadata.parse_record(
                self.context, metadata_record, self.repo)[0]
            if metadata_format == 'xml':
                record.xml = record.xml.decode()
            logger.info(f"identifier: {record.identifier}")
        except Exception as err:
            logger.error(f'Metadata parsing failed: {err}')
            raise

        if self.repo.query_ids([record.identifier]):
            logger.info('Updating record')
            try:
                self.repo.update(record)
                logger.info('record updated')
            except Exception as err:
                logger.error(f'record update failed: {err}')
                raise
        else:
            logger.info('Inserting record')
            try:
                self.repo.insert(record, 'local', util.get_today_and_now())
                logger.info('record inserted')
            except Exception as err:
                logger.error(f'record insertion failed: {err}')
                raise

        return


class ItemBackend(Backend[Item], PycswMixIn):
    def exists(self, source: Source, item: Item) -> bool:
        # TODO: sort out identifier problem in ISO XML
        logger.info(f'Checking for identifier {item.id}')
        if self.repo.query_ids([item.id]):
            logger.info(f'Identifier {item.id} exists')
            return True
        else:
            logger.info(f'Identifier {item.id} does not exist')
            return False

    def register(self, source: Source, item: Item, replace: bool):
        logger.info('Ingesting product')

        assets = item.get_assets()

        # ESA metadata (Sentinel)
        if 'inspire-metadata' in assets and 'product-metadata' in assets:
            inspire_xml = assets['inspire-metadata'].href
            logger.info('Ingesting Sentinel 2 STAC Item')
            # logger.info(f'asset href: {inspire_xml}')
            base_url = f'{os.path.dirname(inspire_xml)}'
            # logger.info(f'base_url: {base_url}')
            imo = STACMetadata(base_url)
            metadata = imo.from_stac_item(
                json.dumps(item.to_dict(transform_hrefs=False)),
                self.ows_url
            )

        # ISO metadata
        elif 'iso-metadata' in assets:
            iso_xml = assets['iso-metadata'].href
            iso_xml_local = '/tmp/iso-metadata.xml'

            logger.info(f"Ingesting ISO XML metadata file: {iso_xml}")

            try:
                source.get_file(iso_xml, iso_xml_local)
            except Exception as err:
                logger.error(err)
                raise

            with open(iso_xml_local, 'r') as a:
                metadata = a.read()

        # Landsat
        elif 'MTL.xml' in assets:
            logger.info('Ingesting Landsat STAC Item')
            mtl_xml = assets['MTL.xml'].href
            base_url = mtl_xml[:mtl_xml.rfind("/")]
            logger.debug(f'base URL {base_url}')
            imo = STACMetadata(base_url)
            metadata = imo.from_stac_item(
                json.dumps(item.to_dict(transform_hrefs=False)),
                self.ows_url
            )

        # Generic STAC Item (Stage out or other)
        else:
            logger.info('Ingesting STAC Item')
            if item.get_links('self'):
                self_href = item.get_links('self')[0].get_absolute_href()
                parsed = urlparse(self_href)
                parsed = parsed._replace(path=os.path.dirname(parsed.path))
                base_url = urlunparse(parsed)
            else:
                base_url = ''

            logger.debug(f'base URL {base_url}')
            imo = STACMetadata(base_url)
            metadata = imo.from_stac_item(
                json.dumps(item.to_dict(transform_hrefs=False)),
                self.ows_url
            )

        logger.debug(f'Upserting metadata: {metadata}')
        self._parse_and_upsert_metadata(metadata)

    def deregister(self, source: Optional[Source], item: Item):
        self.deregister_identifier(item.id)

    def deregister_identifier(self, identifier: str):
        logger.info(f'Deleting record {identifier}')
        # TODO: identifier alignment required with other components
        if self.repo.query_ids([identifier]):
            logger.debug('found matching identifier')
            identifier = identifier
        else:
            logger.debug('did not find matching identifier, adding .SAFE')
            identifier = f'{identifier}.SAFE'

        constraint = {
            'type': 'filter',
            'values': [identifier],
            'where': 'identifier = :pvalue0'
        }
        try:
            rows = self.repo.delete(constraint)
            logger.info(f'{rows} records deleted')
        except Exception as err:
            logger.error(f'delete failed: {err}')
            raise

        return identifier


class CWLBackend(Backend[dict], PycswMixIn):
    def exists(self, source: Optional[Source], item: dict) -> bool:
        pass

    def register(self, source: Optional[Source], item: dict, replace: bool):
        logger.info('Ingesting CWL')
        cwl_local = '/tmp/cwl.yaml'

        path = item["url"]
        source.get_file(path, cwl_local)
        with open(cwl_local) as f:
            logger.debug(f'base URL {path}')
            base_url = f's3://{path}'
            imo = ISOMetadata(base_url)
            parsed = urlparse(self.public_s3_url)
            if len(parsed.path.split(':')) > 1:
                new_path = parsed.path.split(':')[0] + ':' + path
            else:
                new_path = os.path.join(parsed.path, path)
            new_scheme = f'{parsed.scheme}://{parsed.netloc}'
            public_url = urljoin(new_scheme, new_path)
            iso_metadata = imo.from_cwl(
                f.read(), public_url, item.get("parent_identifier")
            )

        logger.debug(f"Removing temporary file {cwl_local}")

        os.remove(cwl_local)
        logger.debug(f'Upserting metadata: {iso_metadata}')
        self._parse_and_upsert_metadata(iso_metadata)

    def deregister(self, source: Optional[Source], item: dict):
        pass

    def deregister_identifier(self, identifier: str):
        pass


class ADESBackend(Backend[dict], PycswMixIn):
    def exists(self, source: Optional[Source], item: dict) -> bool:
        pass

    def register(self, source: Optional[Source], item: dict, replace: bool):
        if (item["type"] == 'ades'):
            logger.info('Ingesting ADES')
        else:
            logger.info('Ingesting OGC API - Processes')
        base_url = item["url"]
        logger.debug(f'base URL {base_url}')
        imo = ISOMetadata(base_url)
        iso_metadata_records = imo.from_oaproc(
            item.get("parent_identifier"), item.get("type"))
        for iso_metadata in iso_metadata_records:
            logger.debug(f'Upserting metadata: {iso_metadata}')
            self._parse_and_upsert_metadata(iso_metadata)

    def deregister(self, source: Optional[Source], item: dict):
        pass

    def deregister_identifier(self, identifier: str):
        pass


class CollectionBackend(Backend[Collection], PycswMixIn):
    def exists(self, source: Optional[Source], item: dict) -> bool:
        pass

    def register(
        self, source: Optional[Source], item: Collection, replace: bool
    ):
        logger.info('Ingesting Collection')
        imo = STACMetadata("")
        metadata = imo.from_stac_collection(item.to_dict(False, False))
        logger.info(f'Upserting metadata: {metadata}')
        self._parse_and_upsert_metadata(metadata)

    def deregister(self, source: Optional[Source], item: Collection):
        pass

    def deregister_identifier(self, identifier: str):
        pass


class CatalogueBackend(Backend[dict], PycswMixIn):
    def exists(self, source: Optional[Source], item: dict) -> bool:
        pass

    def register(
        self, source: Optional[Source], item: Collection, replace: bool
    ):
        logger.info('Ingesting Catalogue')
        # OARec
        # CSW2
        # CSW3
        # STAC API
        # OpenSearch

        base_url = item['url']
        imo = ISOMetadata(base_url)
        metadata = None

        try:
            is_stac_api = False
            c = Records(base_url)
            logger.info('Detected OGC API - Records')

            try:
                client = Client.open(base_url)
                logger.info('Detected STAC API')
                is_stac_api = True
            except:
                logger.info('STAC API client failed')

            # if 'stac_version' in c.response:
            #     logger.info('Detected STAC API')
            #     is_stac_api = True

            metadata = imo.from_oarec(c.response, is_stac_api=is_stac_api)

        except JSONDecodeError:
            try:
                c = CatalogueServiceWeb(base_url)
                logger.info('Detected OGC CSW')
                metadata = imo.from_csw()
            except etree.XMLSyntaxError:
                try:
                    client = Client.open(base_url)
                    logger.info('Detected STAC Catalog')
                    metadata = imo.from_stac_catalog(base_url)
                except JSONDecodeError:
                    logger.info('All catalogue clients failed')
            except RuntimeError:
                try:
                    osearch = OpenSearch(base_url)
                    logger.info('Detected OpenSearch Catalog')
                    metadata = imo.from_opensearch(base_url)
                except:
                    logger.info('All catalogue clients failed')

        logger.info(f'Upserting metadata: {metadata}')
        self._parse_and_upsert_metadata(metadata)

    def deregister(self, source: Optional[Source], item: Collection):
        pass

    def deregister_identifier(self, identifier: str):
        pass


class JSONBackend(Backend[dict], PycswMixIn):
    def exists(self, source: Optional[Source], item: dict) -> bool:
        pass

    def register(
        self, source: Optional[Source], item: dict, replace: bool
    ):
        logger.info('Ingesting JSON')
        logger.info(f'Upserting metadata: {item}')
        self._parse_and_upsert_metadata(json.dumps(item))

    def deregister(self, source: Optional[Source], item: dict):
        pass

    def deregister_identifier(self, identifier: str):
        pass


class XMLBackend(Backend[dict], PycswMixIn):
    def exists(self, source: Optional[Source], item: dict) -> bool:
        pass

    def register(
        self, source: Optional[Source], item: dict, replace: bool
    ):
        logger.info('Ingesting XML')
        path = item["url"]
        xml_local = '/tmp/metadata.xml'
        logger.debug(f"Downloading {path} to temporary file {xml_local}")
        if source:
            source.get_file(path, xml_local)
        else:
            r = requests.get(path, allow_redirects=True)
            open(xml_local, 'wb').write(r.content)
        with open(xml_local) as f:
            xml = f.read()
        logger.debug(f"Removing temporary file {xml_local}")
        os.remove(xml_local)
        logger.info(f'Upserting metadata: {xml}')
        self._parse_and_upsert_metadata(xml)

    def deregister(self, source: Optional[Source], item: dict):
        pass

    def deregister_identifier(self, identifier: str):
        pass
