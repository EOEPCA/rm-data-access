#------------------------------------------------------------------------------
#
# Project: prism view server
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (C) 2020-2023 EOX IT Services GmbH <https://eox.at>
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
FROM registry.gitlab.eox.at/vs/vs/core:release-4.1.3

LABEL name="EOEPCA data access core" \
      vendor="EOX IT Services GmbH <https://eox.at>" \
      license="MIT Copyright (C) 2019 EOX IT Services GmbH <https://eox.at>" \
      type="EOEPCA data access core" \
      version="1.4-dev1"

RUN pip3 install PyYAML "SQLAlchemy<2.0.0" OWSLib pygeometa pystac_client && \
    pip3 install https://github.com/geopython/pycsw/archive/master.zip

RUN apt-get update \
  && apt-get install -y wget \
  && apt-get autoremove -y \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/partial/* /tmp/* /var/tmp/*

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

# Patching EOxServer 1.2.12 release
ADD eoxserver.patch /opt/eoxserver/
RUN cd /opt/eoxserver && patch -p 1 < eoxserver.patch

# FIXME: Patching EOxServer 1.2.12 release prometheus configuration
ENV PROMETHEUS_MULTIPROC_DIR="/var/tmp/prometheus_multiproc_dir"
RUN mkdir -p $PROMETHEUS_MULTIPROC_DIR && \
    chmod 777 $PROMETHEUS_MULTIPROC_DIR

ENV STARTUP_SCRIPTS="/registrar_pycsw/registrar_pycsw/initialize-collections.sh"
