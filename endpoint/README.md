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


3. send a POST request to `http://127.0.0.1:85/userinfo` contains the encoded JWT token.