### Endpoint Testing 



1. Build the image:


```bash
# in root dir
docker build endpoint/ -t exp-app

```



2. run the container:

```bash
docker run -p 85:8000 exp-app

```


3. Send a curl request with the `jwt_token` e.g: 
```bash
curl -H "Accept: */*" -H "Authorization: Bearer <jwt_token>" http://127.0.0.1:85/userinfo

```