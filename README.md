# LOVE-producer

## Basic usage - Running locally
Follow these instructions to run the parts of the producer locally

### Running Telemetry Producer
Note: these steps are not necessary if you are working with LOVE-integration-tools and this repo (LOVE-backend) as submodule.

Prepare needed repositories
```
mkdir -p $HOME/UW/LSST/tsrepos
cd $HOME/UW/LSST/tsrepos
git clone https://github.com/lsst-ts/ts_sal
git clone https://github.com/lsst-ts/ts_xml
git clone https://github.com/lsst-ts/salobj
```

Checkout to a safe commit
```
cd ts_sal
git checkout b16c2900df2b09ab33719320a280c62bc8da825e
```
Build the image

```
docker build -t telemetry-producer .
```

Run container
```
docker run -it --rm --name opsim \
    -v $HOME/.config:/home/opsim/.config \
    -v $HOME/UW/LSST/tsrepos/:/home/opsim/tsrepos \
    -e OPSIM_HOSTNAME=rowen_mac \
    -e DISPLAY=127.0.0.1:0 \
    -p 8884:8884 \
    --expose=8000 \
    --net="host" \
    telemetry-producer \
    /home/opsim/start.sh
```



### Running SalObj

#### Generate SALpy libraries from oboberg/salmaker:latest
Prepare docker scripts
```
mkdir -p $HOME/UW/Config
cp -r docker $HOME/UW/Config/
```
Prepare needed repositories
```
mkdir -p $HOME/UW/LSST/tsrepos
cd $HOME/UW/LSST/tsrepos
git clone https://github.com/lsst-ts/ts_sal
git clone https://github.com/lsst-ts/ts_xml
git clone https://github.com/lsst-ts/salobj
```

Checkout to a safe commit
```
cd ts_sal
git checkout b16c2900df2b09ab33719320a280c62bc8da825e
```

Run container
```
docker run -it --rm --name salmaker \
    -v $HOME/.config:/home/opsim/.config \
    -v $HOME/UW/LSST/tsrepos:/home/opsim/tsrepos \
    -v $HOME/UW/Config/docker/fix_salmaker:/home/opsim/fix_salmaker \
    -e OPSIM_HOSTNAME=rowen_mac \
    -e DISPLAY=127.0.0.1:0 \
    -p 8882:882 \
    oboberg/salmaker:latest \
    /home/opsim/fix_salmaker/start.sh
```

Build libraries
```
./build_topics.sh
```

#### Run opsim container from oboberg/opsim4_fbs_py3:latest
Execute
```
docker run -it --rm --name opsim \
    -v $HOME/.config:/home/opsim/.config \
    -v $HOME/UW/LSST/tsrepos/:/home/opsim/tsrepos \
    -v $HOME/UW/Config/docker/fix_opsim:/home/opsim/fix_opsim \
    -e OPSIM_HOSTNAME=rowen_mac \
    -e DISPLAY=127.0.0.1:0 \
    -p 8884:8884 \
    oboberg/opsim4_fbs_py3:latest \
    /home/opsim/fix_opsim/simple_start.sh
```

Copy libraries from salmaker container
```
docker cp salmaker:/home/opsim/sal_libs .
docker cp sal_libs opsim:/home/opsim
rm -rf sal_libs
```

Copy files from lib folder to proper one (from opsim container)
```
cp /home/opsim/sal_libs/* dds/lib/
```

Install SALobj library
```
cd /home/opsim/tsrepos/salobj
setup -r .
scons
scons install declare
```

### Running LDAP server
Create `var/lib/ldap` and `etc/ldap/slapd.d` folders
```
docker run -v /home/ec2-user/var/lib/ldap:/var/lib/ldap -v /home/ec2-user/etc/ldap/slapd.d:/etc/ldap/slapd.d -e LDAP_ORGANISATION="Inria Chile" -e LDAP_DOMAIN="inria.cl" -e LDAP_ADMIN_PASSWORD="lala" -d -p 389:389 -p 636:636 osixia/openldap
```
