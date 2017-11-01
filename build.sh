set -e

log () {
    ORANGE='\033[0;33m'
    NC='\033[0m'
    echo -e "${ORANGE}${*}${NC}"
}


if [ ! -d pyalsaaudio-0.8.4/ ]; then
    log "\n→ Downloading pyalsaaudio..."
    wget https://pypi.python.org/packages/52/b6/44871791929d9d7e11325af0b7be711388dfeeab17147988f044a41a6d83/pyalsaaudio-0.8.4.tar.gz#md5=b46f69561bc85fc52e698b2440ca251e
    tar xzf pyalsaaudio-0.8.4.tar.gz
fi

log "\n→ Building pyalsaaudio..."
pushd pyalsaaudio-0.8.4/
python2 setup.py build
cp build/lib.*/*.so ../gum/alsaaudio.so
rm -rf pyalsaaudio*
popd

log "\n→ Building scikits.samplerate..."
pushd gum/scikits/samplerate
make
popd

log "\n→ Building fast waveform display..."
pushd gum/fast
make
popd

log "\n→ Building fast waveform display..."
pushd gum/fx
make
popd

log "\n✓ Build completed with success"
