FROM ghcr.io/inti-cmnb/kicad10_auto_full:dev
LABEL AUTHOR="Salvador E. Tropea <stropea@inti.gob.ar>"
LABEL Description="Export various files from KiCad projects (KiCad 10 + development)"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /mnt

ENTRYPOINT [ "/entrypoint.sh" ]
