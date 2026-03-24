# Build stage
FROM node:22-slim AS builder

WORKDIR /app

# Copy package manifest (fresh resolve for correct platform binaries)
COPY package.json ./

# Install dependencies
RUN npm install --no-audit --no-fund

# Copy source files
COPY . .

# Accept build arguments
ARG VITE_API_BASE_URL=http://localhost:9095
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the application
RUN npm run build

# Production stage - just copy the build output
FROM node:22-slim

WORKDIR /app

# Copy built assets from builder (includes everything needed)
COPY --from=builder /app/.output ./.output

# Expose port
EXPOSE 3000

# Start the application
CMD ["node", ".output/server/index.mjs"]
