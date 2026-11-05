FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .
RUN npm run build

FROM busybox:1.37 AS site

COPY --from=build /app/build /site
CMD ["sh", "-c", "cp -R /site/_astro /out/ && find /out/_astro -type f -mtime +7 -delete && cp -R /site/. /out/"]
