# LOVE-producer

This repository contains the code of the LOVE-producer application, that acts as middleware between the LOVE-manager and SAL.

See the documentation here: https://lsst-ts.github.io/LOVE-producer/html/index.html

## 1. Use as part of the LOVE system

In order to use the LOVE-producer as part of the LOVE system we recommend to use the docker-compose and configuration files provided in the [LOVE-integration-tools](https://github.com/lsst-ts/LOVE-integration-tools) repo. Please follow the instructions there.

## 2. Local load for development

We provide a docker image and a docker-compose file in order to load the LOVE-producer locally for development purposes, i.e. run tests and build documentation.

This docker-compose does not copy the code into the image, but instead it mounts the repository inside the image, this way you can edit the code from outside the docker container with no need to rebuild or restart.

### 2.1 Load and get into the docker image

Follow these instructions to run the application in a docker container and get into it:

```
docker-compose up -d
docker-exec producer bash
```

### 2.2 Run tests

Once inside the container and in the `love` folder you can run the tests as follows:

```
/usr/src/love/producer/run-tests.sh
```

Then press `Ctrl + D`

### 2.3 Build documentation

Once inside the container and in the `love` folder you can build the documentation as follows:

```
source .setup_dev.sh
cd /usr/src/love/docsrc
./create_docs.sh
```

## 3. Developing/Testing with conda/pip

To develop and test the LOVE-producer with conda do the following procedure:

```
conda create -y --name love-dev python=3.8
conda activate love-dev
conda install -y gevent greenlet six websocket-client websockets eventlet
conda install -y -c lsstts ts-salobj=6.4.1 ts-idl=3.1.3_9.1.1_5.1.1 ts-ddsconfig=0.6.2 ts-dds=6.10.4=py38_0 ts-conda-build
pip install kafkit[aiohttp] aiokafka
export TS_CONFIG_OCS_DIR=...
```

### Linting & Formatting
In order to maintaing code linting and formatting we use `pre-commit` that runs **Flake8** (https://flake8.pycqa.org/) and **Black** (https://github.com/psf/black) using Git Hooks. To enable this you have to:

1. Install `pre-commit` in your local development environment:
```
pip install pre-commit
```

2. Set up the git hook scripts running:
```
pre-commit install
```

3. Start developing! Linter and Formatter will be executed on every commit you make