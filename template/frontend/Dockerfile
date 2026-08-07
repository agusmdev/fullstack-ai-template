# ---- Builder stage: install deps + build with bun ----
# Pinned to 1.3.14-debian (matches local bun.lock; tag is >7 days old).
FROM oven/bun:1.3.14-debian AS builder

WORKDIR /app

# Skip the husky "prepare" hook — there is no .git inside the build context.
ENV HUSKY=0

# Copy lockfile + manifest first for layer caching.
COPY package.json bun.lock ./

# Install dependencies (frozen for reproducibility).
RUN bun install --frozen-lockfile

# Copy the rest of the source.
COPY . .

# Build-time API URL. This is browser-facing: the SPA runs in the user's
# browser, which reaches the backend over the host's localhost:9095.
ARG VITE_API_BASE_URL=http://localhost:9095
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the production server bundle (TanStack Start + nitro -> .output/server/index.mjs).
RUN bun run build

# ---- Runtime stage: serve the nitro server with bun ----
# The build runs under bun, so nitro/srvx emit a bun-targeted server bundle
# (Bun.serve). We keep the same runtime to guarantee compatibility.
FROM oven/bun:1.3.14-slim

WORKDIR /app

# Copy build output (server bundle + public assets).
COPY --from=builder /app/.output ./.output

EXPOSE 3000

CMD ["bun", ".output/server/index.mjs"]
