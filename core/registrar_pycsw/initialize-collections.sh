#!/usr/bin/env bash


python3 -c "
from registrar.backend import get_backends
from registrar.config import load_config

config = load_config('/config.yaml')
for backend in get_backends(config, ''):
    if isinstance(backend, PycswBackend):
        print('Loading collection metadata')
        backend.load_collection_level_metadata()
"
