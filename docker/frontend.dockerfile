FROM --platform=$BUILDPLATFORM node:24-alpine AS build

WORKDIR /app
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 ASTRO_TELEMETRY_DISABLED=1
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.cache/node/corepack \
    --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

COPY . .
RUN --mount=type=cache,target=/root/.cache/node/corepack pnpm check && pnpm build

FROM busybox:1.37 AS site

COPY --from=build /app/build /site
CMD ["sh", "-c", "cp -R /site/_astro /out/ && find /out/_astro -type f -mtime +7 -delete && cp -R /site/. /out/"]
