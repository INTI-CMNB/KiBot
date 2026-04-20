#!/bin/sh
set -e
export HASH=`git log --pretty=format:%h -1 | tr -d '\n'`
docker build -f Dockerfile --build-arg repo_hash=${HASH} -t ghcr.io/inti-cmnb/kicad9_auto_full:dev .
TG1=`docker run --rm ghcr.io/inti-cmnb/kicad10_auto_full:dev kibot --version | sed 's/.* \([0-9]\+\.[0-9]\+\.[0-9]\+\(\.[0-9]\+\)\?\) .*/\1/' | tr -d '\n'`
TG2=k`docker run --rm ghcr.io/inti-cmnb/kicad10_auto_full:dev kicad_version.py`
TG3=d`docker run --rm ghcr.io/inti-cmnb/kicad10_auto_full:dev cat /etc/debian_version | tr -d '\n'`
TG4=b`docker run --rm ghcr.io/inti-cmnb/kicad10_auto_full:dev /bin/bash -c "blender --version | head -n 1 | tr -d 'Blender '"`
docker tag ghcr.io/inti-cmnb/kicad10_auto_full:dev ghcr.io/inti-cmnb/kicad10_auto_full:dev_${TG1}-${HASH}_${TG2}_${TG3}_${TG4}
docker tag ghcr.io/inti-cmnb/kicad10_auto_full:dev ghcr.io/inti-cmnb/kicad_auto_full:dev_k10_${TG1}-${HASH}_${TG2}_${TG3}_${TG4}
docker tag ghcr.io/inti-cmnb/kicad10_auto_full:dev ghcr.io/inti-cmnb/kicad_auto_full:dev_k10
docker push ghcr.io/inti-cmnb/kicad10_auto_full:dev_${TG1}-${HASH}_${TG2}_${TG3}_${TG4}
docker push ghcr.io/inti-cmnb/kicad_auto_full:dev_k10_${TG1}-${HASH}_${TG2}_${TG3}_${TG4}
docker push ghcr.io/inti-cmnb/kicad_auto_full:dev_k10
docker push ghcr.io/inti-cmnb/kicad10_auto_full:dev
