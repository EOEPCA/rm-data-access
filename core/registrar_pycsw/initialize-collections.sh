#!/usr/bin/env bash


python3 -c "
from registrar.backend import get_backends
from registrar.config import RegistrarConfig
from registrar_pycsw.backend import PycswMixIn, ItemBackend

config = RegistrarConfig.from_file(open('/config.yaml'))

for backend in get_backends(config.routes['items'].backends):
    if isinstance(backend, ItemBackend):
        print('Loading collection metadata')
        backend.load_collection_level_metadata()
"
