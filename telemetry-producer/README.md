Command for development, adding dev_producer folder to /home/opsim/ as a volume, so it can synchronize with the host folder

`
docker run -it --rm --name opsim    -v $HOME/gitrepos/LOVE-backend/telemetry-producer/producer:/home/opsim/dev_producer -v $HOME/.config:/home/opsim/.config     -v $HOME/UW/LSST/tsrepos/:/home/opsim/tsrepos    -e OPSIM_HOSTNAME=rowen_mac     -e DISPLAY=127.0.0.1:0     -p 8884:8884     --expose=8000     --net="host"     telemetry-producer     /home/opsim/start.sh
`
