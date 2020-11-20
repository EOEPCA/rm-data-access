from pycsw.core import metadata, repository, util
import pycsw.core.admin
import pycsw.core.config

from .metadata import gen_iso_metadata


logger = logging.getLogger(__name__)


class PycswBackend(Backend):
    def __init__(self, instance_base_path: str, instance_name: str, mapping: dict, simplify_footprint_tolerance: int=None):
        logger.debug('Setting up static context')
        self.context = pycsw.core.config.StaticContext()

        logger.debug('Initializing pycsw repository')
        self.repo = repository.Repository(os.environ.get('PYCSW_REPOSITORY_DATABASE_URI'), self.context, table='records')

    def exists(self, source: Source, item: Context) -> bool:
        # TODO: sort out identifier problem in ISO XML
        logger.info(self.repo.query(constraint={}))
        if self.repo.query_ids([item.identifier]):
            logger.info('identifier exists')
            return True
        return False

    def register(self, source: Source, item: Context, replace: bool) -> RegistrationResult:
        ingest_fail = False
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
        with open(esa_xml_local, 'rb') as a, open(inspire_xml_local, 'rb') as b:
             iso_metadata = gen_iso_metadata(base_url, a.read(), b.read())

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
