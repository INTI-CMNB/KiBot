#!/bin/sh
set -e
HASH=`git log --pretty=format:%h -1 | tr -d '\n'`
docker build -f Dockerfile --build-arg repo_hash=${HASH} -t ghcr.io/inti-cmnb/kicad9_auto:dev .
TG1=`docker run --rm ghcr.io/inti-cmnb/kicad9_auto:dev kibot --version | sed 's/.* \([0-9]\+\.[0-9]\+\.[0-9]\+\(\.[0-9]\+\)\?\) .*/\1/' | tr -d '\n'`
TG2=k`docker run --rm ghcr.io/inti-cmnb/kicad9_auto:dev kicad_version.py`
TG3=d_sid
docker tag ghcr.io/inti-cmnb/kicad9_auto:dev ghcr.io/inti-cmnb/kicad9_auto:dev_${TG1}-${HASH}_${TG2}_${TG3}
docker tag ghcr.io/inti-cmnb/kicad9_auto:dev ghcr.io/inti-cmnb/kicad_auto:dev_k9_${TG1}-${HASH}_${TG2}_${TG3}
docker tag ghcr.io/inti-cmnb/kicad9_auto:dev ghcr.io/inti-cmnb/kicad_auto:dev_k9
docker push ghcr.io/inti-cmnb/kicad9_auto:dev_${TG1}-${HASH}_${TG2}_${TG3}
docker push ghcr.io/inti-cmnb/kicad_auto:dev_k9_${TG1}-${HASH}_${TG2}_${TG3}
docker push ghcr.io/inti-cmnb/kicad_auto:dev_k9
docker push ghcr.io/inti-cmnb/kicad9_auto:dev
