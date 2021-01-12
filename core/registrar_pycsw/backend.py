import os
import logging

from lxml import etree
from pycsw.core import metadata, repository, util
import pycsw.core.admin
import pycsw.core.config
from registrar.backend import Backend, RegistrationResult
from registrar.source import Source
from registrar.context import Context

from .metadata import ISOMetadata


logger = logging.getLogger(__name__)


class PycswBackend(Backend):
    def __init__(self, repository_database_uri):
        logger.debug('Setting up static context')
        self.context = pycsw.core.config.StaticContext()

        logger.debug('Initializing pycsw repository')
        self.repo = repository.Repository(repository_database_uri, self.context, table='records')

    def exists(self, source: Source, item: Context) -> bool:
        # TODO: sort out identifier problem in ISO XML
        logger.info(self.repo.query(constraint={}))
        if self.repo.query_ids([item.identifier]):
            logger.info('identifier exists')
            return True
        return False

    def register(self, source: Source, item: Context, replace: bool) -> RegistrationResult:
        # For path for STAC items
        ingest_fail = False
        if item.scheme == 'stac-item':
            stac_item_local = '/tmp/item.json'
            source.get_file(item.path, stac_item_local)
            with open(stac_item_local) as f:
                base_url = 's3://{}'.format(os.path.split(os.path.dirname(item.path))[0])
                imo = ISOMetadata(base_url)
                iso_metadata = imo.from_stac_item(f.read())

            logger.debug(f"Removing temporary file {stac_item_local}")
            os.remove(stac_item_local)

        else:
            esa_xml_local = '/tmp/esa-metadata.xml'
            inspire_xml_local = '/tmp/inspire-metadata.xml'

            esa_xml = item.metadata_files[0]
            logger.info(f"ESA XML metadata file: {esa_xml}")

            inspire_xml = os.path.dirname(item.metadata_files[0]) + "/INSPIRE.xml"
            logger.info(f"INSPIRE XML metadata file: {inspire_xml}")

            base_url = 's3://{}'.format(os.path.split(os.path.dirname(esa_xml))[0])

            try:
                source.get_file(inspire_xml, inspire_xml_local)
                source.get_file(esa_xml, esa_xml_local)
            except Exception as err:
                logger.error(err)
                return False

            logger.info('Generating ISO XML based on ESA and INSPIRE XML')
            imo = ISOMetadata(base_url)
            with open(esa_xml_local, 'rb') as a, open(inspire_xml_local, 'rb') as b:
                iso_metadata = imo.from_esa_iso_xml(a.read(), b.read())

            for tmp_file in [esa_xml_local, inspire_xml_local]:
                logger.debug(f"Removing temporary file {tmp_file}")
                os.remove(tmp_file)

        logger.debug('Parsing XML')
        try:
            xml = etree.fromstring(iso_metadata)
        except Exception as err:
            logger.error('XML parsing failed: {}'.format(err))
            return False

        logger.debug('Processing metadata')
        try:
            record = metadata.parse_record(self.context, xml, self.repo)[0]
            record.xml = record.xml.decode()
            logger.info(f"identifier: {record.identifier}")
        except Exception as err:
            logger.error('Metadata parsing failed: {}'.format(err))
            return False

        logger.debug('Inserting record')
        try:
            self.repo.insert(record, 'local', util.get_today_and_now())
            logger.info('record inserted')
        except Exception as err:
            ingest_fail = True
            logger.error('record insertion failed: {}'.format(err))

        if ingest_fail and replace:
            logger.info('Updating record')
            try:
                self.repo.update(record)
                logger.info('record updated')
            except Exception as err:
                logger.error('record update failed: {}'.format(err))

        return True
