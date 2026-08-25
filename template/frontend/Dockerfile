# syntax=docker/dockerfile:1.7

# ---------------------------------------------------------------------------
# Stage 1 — install node_modules from the committed bun.lock.
# The project is a bun project (see .cta.json); `npm install` cannot resolve
# this dependency tree and has no lockfile to work from.
# ---------------------------------------------------------------------------
FROM oven/bun:1.3.14-slim AS deps

WORKDIR /app

# Dependency layer: only invalidated when the manifests change.
COPY package.json bun.lock ./
RUN --mount=type=cache,target=/root/.bun/install/cache,sharing=locked \
    bun install --frozen-lockfile --ignore-scripts

# ---------------------------------------------------------------------------
# Stage 2 — build the Nitro server bundle.
# ---------------------------------------------------------------------------
FROM oven/bun:1.3.14-slim AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG VITE_API_BASE_URL=http://localhost:9095
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    NODE_ENV=production

RUN bun run build

# ---------------------------------------------------------------------------
# Stage 3 — runtime. Only the self-contained .output bundle ships.
# Nitro emits a Bun server entry when it builds under Bun, so the runtime is
# Bun too — which also means no second base image to pull.
# ---------------------------------------------------------------------------
FROM oven/bun:1.3.14-slim AS runtime

ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000

WORKDIR /app
COPY --from=builder --chown=bun:bun /app/.output ./.output

USER bun
EXPOSE 3000

CMD ["bun", "run", ".output/server/index.mjs"]
