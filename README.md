<!--
***
*** To avoid retyping too much info. Do a search and replace for the following:
*** rm-data-access, twitter_handle, email
-->

<!-- PROJECT SHIELDS -->
<!--
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
![Build][build-shield]

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/EOEPCA/rm-data-access">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">EOEPCA Data Access</h3>

  <p align="center">
    This repository includes the EOEPCA Data Access building block
    <br />
    <a href="https://github.com/EOEPCA/rm-data-access"><strong>Explore the docs »</strong></a>
    <br />
    <a href="https://github.com/EOEPCA/rm-data-access">View Demo</a>
    ·
    <a href="https://github.com/EOEPCA/rm-data-access/issues">Report Bug</a>
    ·
    <a href="https://github.com/EOEPCA/rm-data-access/issues">Request Feature</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->

## Table of Contents

- [Description](#description)
  - [Built With](#built-with)
  - [Interfaces](#interfaces)
- [Getting Started](#getting-started)
  - [Deployment](#deployment)
- [Documentation](#documentation)
- [Usage](#usage)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgements](#acknowledgements)

<!-- ABOUT THE PROJECT -->

## Description

The EOEPCA Data Access building block is built upon the upstream View Server project.

View Server is a Docker based software and all of its components are distributed and executed in context of Docker images, containers and Helm charts. Basic knowledge of Docker and either Docker Swarm or Helm and Kubernetes is a prerequisite.

The provided external services are services for searching, viewing, and downloading of Earth Observation (EO) data. Service endpoints optimized for performance as well as for flexibility are provided alongside each other.

The View Server default Chart vs consists of the following service components (with their respective Docker image in parenthesis):

* Web Client (client)
* Cache (cache)
* Renderer (core)
* Registrar (core)
* Seeder (seeder)
* Preprocessor (preprocessor)
* Ingestor (ingestor)
* Harvester (harvester)
* Scheduler (scheduler)
* Database (postgis)
* Queue Manager (redis)

View Server is Open Source, released under an MIT license.

This [repository](https://github.com/EOEPCA/rm-data-access) holds EOEPCA customizations for the View Server Core component (Renderer and Registrar)
EOEPCA customizations for the Harvester component can be found in https://github.com/EOEPCA/rm-harvester

[![Product Name Screen Shot][product-screenshot]](https://gitlab.eox.at/vs/vs)

### Built With

- [Python](https://www.python.org/)
- [Django](https://www.djangoproject.com/)
- [GDAL](https://gdal.org/)
- [PostGIS](https://postgis.net/)
- [EOXServer](https://github.com/EOxServer/eoxserver)
- [EOX View Server](https://gitlab.eox.at/vs/vs)

### Interfaces

The Data Access provides the following interfaces:
* OGC WMS 1.1/1.3 (EO-WMS)
* OGC WCS 2.0.0 (EO Application Profile)
* OGC WMTS 1.0
* DSEO
* OpenSearch with OGC EO, Geo and Time extensions


<!-- GETTING STARTED -->

## Getting Started

To get a View Server copy up and running follow these simple steps.

https://vs.pages.eox.at/vs/operator/k8s.html#operating-k8s

### Deployment

Data Access deployment is described [here](https://deployment-guide.docs.eoepca.org/current/eoepca/data-access/) in the [EOEPCA Deployment Guide](https://deployment-guide.docs.eoepca.org/current/eoepca/data-access/).

## Documentation

The View Server documentation can be found at https://vs.pages.eox.at/vs/.

EOEPCA related documents:
* [Data Access Interface Control Document](https://eoepca.github.io/rm-data-access//ICD/)
* [Data Access Software Design Document](https://eoepca.github.io/rm-data-access/SDD/)

The component documentation can be found at https://eoepca.github.io/rm-data-access/.


<!-- USAGE EXAMPLES -->

## Usage

You can find some usage examples in the View Server Client documentation: https://vs.pages.eox.at/vs/user/webclient.html

<!-- ROADMAP -->

## Roadmap

See the [open issues](https://github.com/EOEPCA/rm-data-access/issues) for a list of proposed features (and known issues).

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- LICENSE -->

## License

Distributed under the Apache-2.0 License. See `LICENSE` for more information.

<!-- CONTACT -->

## Contact

Project Link: [https://github.com/EOEPCA/rm-data-access](https://github.com/EOEPCA/rm-data-access)

<!-- ACKNOWLEDGEMENTS -->

## Acknowledgements

- README.md is based on [this template](https://github.com/othneildrew/Best-README-Template) by [Othneil Drew](https://github.com/othneildrew).

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/EOEPCA/rm-data-access.svg?style=flat-square
[contributors-url]: https://github.com/EOEPCA/rm-data-access/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/EOEPCA/rm-data-access.svg?style=flat-square
[forks-url]: https://github.com/EOEPCA/rm-data-access/network/members
[stars-shield]: https://img.shields.io/github/stars/EOEPCA/rm-data-access.svg?style=flat-square
[stars-url]: https://github.com/EOEPCA/rm-data-access/stargazers
[issues-shield]: https://img.shields.io/github/issues/EOEPCA/rm-data-access.svg?style=flat-square
[issues-url]: https://github.com/EOEPCA/rm-data-access/issues
[license-shield]: https://img.shields.io/github/license/EOEPCA/rm-data-access.svg?style=flat-square
[license-url]: https://github.com/EOEPCA/rm-data-access/blob/master/LICENSE
[build-shield]: https://www.travis-ci.com/EOEPCA/rm-data-access.svg?branch=master
[product-screenshot]: images/screenshot.png
