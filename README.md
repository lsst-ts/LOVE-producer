# LOVE-backend
## Running SalObj

### Generate SALpy libraries from oboberg/salmaker:latest
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
