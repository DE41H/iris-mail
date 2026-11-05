FROM caddy:2-alpine

COPY caddyfile /etc/caddy/Caddyfile

ENV XDG_CONFIG_HOME=/config XDG_DATA_HOME=/data
RUN chown -R 10002:10002 /config /data
USER 10002
