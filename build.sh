set -e

log () {
    ORANGE='\033[0;33m'
    NC='\033[0m'
    echo -e "${ORANGE}${*}${NC}"
}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

log "\n→ Creating virtualenv..."
rm -rf venv
virtualenv -p python2 --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt

log "\n→ Building fast waveform display..."
pushd gum/fast
make clean && make
popd

log "\n→ Building audio effects..."
pushd gum/fx
make clean && make
popd

log "\n✓ Build completed with success"
