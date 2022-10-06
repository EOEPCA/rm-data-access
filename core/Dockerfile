#------------------------------------------------------------------------------
#
# Project: prism view server
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (C) 2020 EOX IT Services GmbH <https://eox.at>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#-----------------------------------------------------------------------------

# TODO: make this from a specific release, once released
FROM registry.gitlab.eox.at/vs/core:release-3.2.5-alpha3

LABEL name="EOEPCA data access core" \
      vendor="EOX IT Services GmbH <https://eox.at>" \
      license="MIT Copyright (C) 2019 EOX IT Services GmbH <https://eox.at>" \
      type="EOEPCA data access core" \
      version="1.1.6"

RUN pip3 install PyYAML SQLAlchemy OWSLib pygeometa==0.9.1 && \
    pip3 install https://github.com/geopython/pycsw/archive/master.zip

RUN mkdir /registrar_pycsw
ADD registrar_pycsw/ \
    /registrar_pycsw/registrar_pycsw
ADD setup.py \
    /registrar_pycsw
ADD MANIFEST.in \
    /registrar_pycsw

RUN cd /registrar_pycsw && \
    python3 setup.py install && \
    pip3 install .

ENV STARTUP_SCRIPTS="/registrar_pycsw/registrar_pycsw/initialize-collections.sh"
