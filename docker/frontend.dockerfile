FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .
RUN npm run build

FROM caddy:2-alpine

COPY --from=build /app/build /srv

ENV XDG_CONFIG_HOME=/config XDG_DATA_HOME=/data
RUN chown -R 10002:10002 /config /data
USER 10002
