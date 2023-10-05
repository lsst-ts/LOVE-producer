# LOVE-producer

This repository contains the code of the LOVE-producer application, that acts as middleware between the LOVE-manager and SAL.

See the documentation here: https://love-producer.lsst.io/

## Initialize Environment variables

In order to use the LOVE-producer, some environment variables must be defined before it is run.
All these variables are initialized with default variables defined in the :code:`.env` file defined in the corresponding deployment environment at the [LOVE-integration-tools](https://github.com/lsst-ts/LOVE-integration-tools). These are:

- ``LSST_DDS_PARTITION_PREFIX``: Prefix of the DDS partition to use.
- ``PROCESS_CONNECTION_PASS``: Password use to authenticate connections with the LOVE-manager.
- ``LOVE_CSC_PRODUCER``: Name and salindex of the CSC to connect in the format `<CSC>:<salindex>`. E.g. `ATDome:0`.

## Use as part of the LOVE system

In order to use the LOVE-producer as part of the LOVE system we recommend to use the docker-compose and configuration files provided in the [LOVE-integration-tools](https://github.com/lsst-ts/LOVE-integration-tools) repo. Please follow the instructions there.

## Local load for development

We provide docker images and a docker-compose file in order to load the LOVE-producer locally for development purposes, i.e. run tests and build documentation.

This docker-compose does not copy the code into the image, but instead it mounts the repository inside the image, this way you can edit the code from outside the docker container with no need to rebuild or restart.

### Load and get into the docker image

Follow these instructions to run the application in a docker container and get into it:

```
cd docker/
export dev_cycle=develop #Here you can set a specified version of the lsstts/develop-env image
docker-compose up -d --build
docker-compose exec producer bash
```

### Run tests

Once inside the container and in the `love` folder you can run the tests as follows:

```
source /home/saluser/.setup_dev.sh # Here some configurations will be loaded and you will enter another bash. Press [Ctrl + D] to exit the current console, then the love-producer package will be installed and you can continue with the following step
pip install /usr/src/love # This step is necessary in order to install the last version of the package code 
pytest /usr/src/love/tests
```

### Build documentation

Once inside the container and in the `love` folder you can build the documentation as follows:

```
source /home/saluser/.setup_dev.sh
cd /usr/src/love/docsrc
./create_docs.sh
```

## Developing/Testing with conda/pip

To develop and test the LOVE-producer with conda do the following procedure:

```
conda create -y --name love-dev python=3.8
conda activate love-dev
conda install -y gevent greenlet six websocket-client websockets eventlet
conda install -y -c lsstts ts-salobj=6.4.1 ts-idl=3.1.3_9.1.1_5.1.1 ts-ddsconfig=0.6.2 ts-dds=6.10.4=py38_0 ts-conda-build ts-scriptqueue
pip install kafkit[aiohttp] aiokafka
export TS_CONFIG_OCS_DIR=...
```

### Linting & Formatting
This code uses pre-commit to maintain `black` formatting, `mypy`, `isort` and `flake8` compliance. To enable this, run the following commands once (the first removes the previous pre-commit hook):

```
git config --unset-all core.hooksPath
generate_pre_commit_conf
```

For more details on how to use `generate_pre_commit_conf` please follow: https://tssw-developer.lsst.io/procedures/pre_commit.html#ts-pre-commit-conf.