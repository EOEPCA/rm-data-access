import os
import logging

from lxml import etree
from pycsw.core import metadata, repository, util
import pycsw.core.admin
import pycsw.core.config
from pygeometa.core import read_mcf
from pygeometa.schemas.iso19139 import ISO19139OutputSchema
from registrar.backend import Backend, RegistrationResult
from registrar.source import Source
from registrar.context import Context

from .metadata import ISOMetadata

logger = logging.getLogger(__name__)

THISDIR = os.path.dirname(__file__)

COLLECTION_LEVEL_METADATA = f'{THISDIR}/resources'


class PycswBackend(Backend):
    def __init__(self, repository_database_uri):
        self.collections = []
        logger.debug('Setting up static context')
        self.context = pycsw.core.config.StaticContext()

        logger.debug('Initializing pycsw repository')
        self.repo = repository.Repository(repository_database_uri,
                                          self.context, table='records')

    def load_collection_level_metadata(self):
        logger.debug('Loading collection level metadata')
        for clm in os.listdir(COLLECTION_LEVEL_METADATA):
            self.collections.append(clm)
            logger.debug(f'collection metadata file: {clm}')
            clm_ = os.path.join(COLLECTION_LEVEL_METADATA, clm)
            clm_mcf = read_mcf(clm_)
            clm_iso = ISO19139OutputSchema().write(clm_mcf)
            logger.debug(f'Upserting metadata: {clm_}')
            self._parse_and_upsert_metadata(clm_iso)

    def _parse_and_upsert_metadata(self, md):
        logger.debug('Parsing XML')
        try:
            xml = etree.fromstring(md)
        except Exception as err:
            logger.error('XML parsing failed: {}'.format(err))
            raise

        logger.debug('Processing metadata')
        try:
            record = metadata.parse_record(self.context, xml, self.repo)[0]
            record.xml = record.xml.decode()
            logger.info(f"identifier: {record.identifier}")
        except Exception as err:
            logger.error('Metadata parsing failed: {}'.format(err))
            raise

        if self.repo.query_ids([record.identifier]):
            logger.info('Updating record')
            try:
                self.repo.update(record)
                logger.info('record updated')
            except Exception as err:
                logger.error('record update failed: {}'.format(err))
                raise
        else:
            logger.info('Inserting record')
            try:
                self.repo.insert(record, 'local', util.get_today_and_now())
                logger.info('record inserted')
            except Exception as err:
                logger.error('record insertion failed: {}'.format(err))
                raise

        return

    def exists(self, source: Source, item: Context) -> bool:
        # TODO: sort out identifier problem in ISO XML
        logger.info('Checking for identifier {}'.format(item.identifier))
        if self.repo.query_ids([item.identifier]):
            logger.info('Identifier {} exists'.format(item.identifier))
            return True
        else:
            logger.info('Identifier {} does not exist'.format(item.identifier))
            return False

    def register(self, source: Source, item: Context,
                 replace: bool) -> RegistrationResult:
        # For path for STAC items
        if item.scheme == 'stac-item':
            logger.info('Ingesting processing result')
            stac_item_local = '/tmp/item.json'
            source.get_file(item.path, stac_item_local)
            with open(stac_item_local) as f:
                logger.debug('base URL {}'.format(item.path))
                base_url = 's3://{}'.format(os.path.dirname(item.path))
                imo = ISOMetadata(base_url)
                iso_metadata = imo.from_stac_item(f.read(), self.collections)

            logger.debug(f"Removing temporary file {stac_item_local}")
            os.remove(stac_item_local)

        else:
            logger.info('Ingesting product')
            esa_xml_local = '/tmp/esa-metadata.xml'
            inspire_xml_local = '/tmp/inspire-metadata.xml'

            esa_xml = item.metadata_files[0]
            logger.info(f"ESA XML metadata file: {esa_xml}")

            inspire_xml = os.path.dirname(
                item.metadata_files[0]) + "/INSPIRE.xml"

            logger.info(f"INSPIRE XML metadata file: {inspire_xml}")

            logger.debug('base URL {}'.format(item.path))
            base_url = 's3://{}'.format(item.path)

            try:
                source.get_file(inspire_xml, inspire_xml_local)
                source.get_file(esa_xml, esa_xml_local)
            except Exception as err:
                logger.error(err)
                raise

            logger.info('Generating ISO XML based on ESA and INSPIRE XML')
            imo = ISOMetadata(base_url)

            with open(esa_xml_local, 'rb') as a, open(inspire_xml_local, 'rb') as b:  # noqa
                iso_metadata = imo.from_esa_iso_xml(
                    a.read(), b.read(), self.collections)

            for tmp_file in [esa_xml_local, inspire_xml_local]:
                logger.debug(f"Removing temporary file {tmp_file}")
                os.remove(tmp_file)

        logger.debug(f'Upserting metadata: {iso_metadata}')
        self._parse_and_upsert_metadata(iso_metadata)

        return
