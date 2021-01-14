import os

bind = ['0.0.0.0:8000']
debug = os.environ.get('DEBUG', 'FALSE').upper() == 'TRUE'

