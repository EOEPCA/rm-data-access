import re
import logging
import yaml
from typing import List

from registrar.source import Source
from registrar.context import Context
from registrar.scheme import RegistrationScheme

logger = logging.getLogger(__name__)


class CWLRegistrationScheme(RegistrationScheme):
    name = 'cwl'

    def __init__(self, level_re: str = r'.*(Level_[0-9]+)$'):
        self.level_re = level_re

    def get_context(self, source: Source, path: str) -> List[Context]:

        cwl_filenames = source.list_files(path, ['CWL*.cwl', 'CWL*.CWL'])
        cwl_file = cwl_filenames[0]

        cwl = yaml.load(cwl_file, Loader=yaml.SafeLoader)

        wf = list(filter(lambda x: x['class'] == 'Workflow', cwl['$graph']))[0]

        return [Context(
            identifier=wf['id'],
            path=path,
            scheme=self.name
        )]
