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

    def get_context(self, source: Source, path: str) -> List[Context]:
        cwl_filenames = source.list_files(path, ['*.cwl', '*.CWL'])

        with open(cwl_filenames[0]) as cwl_file:
            cwl = yaml.load(cwl_file, Loader=yaml.SafeLoader)

        workflow = next(iter([
            graph_item
            for graph_item in cwl['$graph']
            if graph_item['class'] == 'Workflow'
        ]), None)

        return [Context(
            identifier=workflow['id'],
            path=path,
            scheme=self.name
        )]
