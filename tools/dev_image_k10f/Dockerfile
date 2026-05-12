FROM ghcr.io/inti-cmnb/kicad_auto_test:ki10
LABEL MAINTAINER="Salvador E. Tropea <stropea@inti.gob.ar>"
LABEL Description="KiCad 10 with KiBot and other automation scripts"

RUN     dpkg --remove kibot && \
	apt-get update && \
	apt-get -y install --no-install-recommends python3-setuptools && \
	curl https://codeload.github.com/INTI-CMNB/KiBot/zip/refs/heads/dev --output pp.zip && \
	unzip pp.zip && \
	curl https://codeload.github.com/yaqwsx/PcbDraw-Lib/zip/refs/heads/master --output pp2.zip && \
	unzip pp2.zip -d KiBot-dev/kibot/resources/pcbdraw/ && \
	rmdir KiBot-dev/kibot/resources/pcbdraw/footprints && \
	mv KiBot-dev/kibot/resources/pcbdraw/PcbDraw-Lib-master KiBot-dev/kibot/resources/pcbdraw/footprints && \
	pip3 install --break-system-packages --no-compile KiBot-dev/ && \
	rm -rf KiBot-dev pp.zip pp2.zip && \
	dpkg --remove kidiff kiauto && \
	curl https://codeload.github.com/INTI-CMNB/KiAuto/zip/refs/heads/master --output pp.zip && \
	unzip pp.zip && \
	pip3 install --break-system-packages KiAuto-master/ && \
	rm -rf KiAuto-master/ pp.zip && \
	curl https://codeload.github.com/INTI-CMNB/KiDiff/zip/refs/heads/master --output pp.zip && \
	unzip pp.zip && \
	pip3 install --break-system-packages KiDiff-master/ && \
	rm -rf KiDiff-master/ pp.zip && \
	rm -rf /var/lib/apt/lists/*

ARG repo_hash
ENV KIBOT_REPO_HASH=$repo_hash
ENV KICAD_AUTO_FULL=1

RUN     kibot --version | sed 's/.* \([0-9]\+\.[0-9]\+\.[0-9]\+\) .*/\1/' | tr -d '\n' > /etc/kiauto_tag && \
	echo -n -${KIBOT_REPO_HASH}_k >> /etc/kiauto_tag && \
	kicad_version.py >> /etc/kiauto_tag && \
	echo -n _d >> /etc/kiauto_tag && \
	cat /etc/debian_version | tr -d '\n' >> /etc/kiauto_tag && \
	echo -n _b >> /etc/kiauto_tag && \
	blender --version | head -n 1 | tr -d 'Blender ' >> /etc/kiauto_tag
