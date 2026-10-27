# The TICKBRON site: the React app built once, then served by Caddy (which also gets the HTTPS
# certificate by itself). The address of the API is part of the build: docker-compose.yml passes
# VITE_API_BASE_URL (https://<DOMAIN from .env>), so changing the domain means building again.
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Only variables that start with VITE_ reach the browser: never put a secret here
ARG VITE_API_BASE_URL
ARG VITE_SATELLITE_TILE_URL
ARG VITE_SATELLITE_ATTRIBUTION
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_SATELLITE_TILE_URL=$VITE_SATELLITE_TILE_URL \
    VITE_SATELLITE_ATTRIBUTION=$VITE_SATELLITE_ATTRIBUTION
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv/www
# The Caddyfile (deploy/Caddyfile) is mounted by docker-compose.yml, so it can change without a rebuild
