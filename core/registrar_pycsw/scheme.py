from os import remove
from os.path import join, basename
import logging
import yaml
from typing import List, Union, Dict
from tempfile import gettempdir

from registrar.source import Source
from registrar.context import Context
from registrar.scheme import RegistrationScheme

logger = logging.getLogger(__name__)


def read_yaml(source: Source, path: str) -> Union[Dict, List]:
    """ Helper to easily read a file on a source as JSON and decode it.
    """
    out_filename = join(gettempdir(), basename(path))
    try:
        source.get_file(path, out_filename)
        with open(out_filename) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
    finally:
        remove(out_filename)
    return data


class CWLRegistrationScheme(RegistrationScheme):
    name = 'cwl'

    def get_context(self, source: Source, path: str) -> List[Context]:
        cwl_filenames = source.list_files(path, ['*.cwl', '*.CWL'])
        cwl = read_yaml(source, cwl_filenames[0])

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
