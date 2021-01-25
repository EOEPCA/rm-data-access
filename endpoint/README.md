### Endpoint Testing


To deploy a working registration instance following [This approach](https://gist.github.com/kalxas/7ca1d3df14f97182db30a02956fdda6b)

## Download staging images


```shell
for i in 'pvs_core' 'pvs_preprocessor' 'pvs_ingestor' 'pvs_cache' 'fluentd' 'pvs_client'; do docker pull registry.gitlab.eox.at/esa/prism/vs/$i:staging;  done;
```

```shell
docker pull eoepca/rm-data-access-core:latest
docker build endpoint/ -t endpoint:latest
```

## Clone PRISM VS git repo

```shell
git clone https://gitlab.eox.at/esa/prism/vs.git prism-vs
cd prism-vs
git checkout staging
cd ..
```

## Clone EOxServer git repo

```shell
git clone https://github.com/EOxServer/eoxserver.git
```

## Clone EOEPCA Resource Management git repo

```shell
git clone https://github.com/EOEPCA/rm-data-access.git eoepca-rm-data-access
```

## Build local registrar image (can be skipped)
```shell
cd eoepca-rm-data-access/core
docker build -t rm-data-access-core:local .
cd ../..
```

## Stop existing docker swarm service

```shell
docker stack rm s2-pvs
```

## Deploy new docker swarm service

```shell
docker network create -d overlay s2-extnet
docker stack deploy -c docker-compose.s2.yml -c docker-compose.s2.dev.yml s2-pvs
```

## Scale preprocessor to zero and check the service

```shell
docker service scale s2-pvs_preprocessor=0
docker service ls
docker stack ps s2-pvs
```


## Ingest one ADES scene from S3 bucket via the registration endpoint and see logs
use the `jwt_token` and the registration item `json_body`

```shell
curl -X POST -H "Accept:Content-Type: application/json" -H "Authorization: Bearer <jwt_token>" -d '<json_body>' http://127.0.0.1:85/register

```

```shell
docker service logs s2-pvs_registrar -f -t

```



## Json request schema

```json
{
    "item": "the storage type : e.g. stac-item",
    "url": "url contains the path to the stored item"
}
```