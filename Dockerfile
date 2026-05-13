FROM ghcr.io/inti-cmnb/kicad8_auto_full:latest
LABEL AUTHOR Salvador E. Tropea <stropea@inti.gob.ar>
LABEL Description="Export various files from KiCad projects (KiCad 8)"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /mnt

ENTRYPOINT [ "/entrypoint.sh" ]
