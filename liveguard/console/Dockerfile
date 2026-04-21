# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup -S next && adduser -S next -G next
COPY --from=build --chown=next:next /app/.next ./.next
COPY --from=build --chown=next:next /app/public ./public
COPY --from=build --chown=next:next /app/package.json ./package.json
COPY --from=build --chown=next:next /app/node_modules ./node_modules
COPY --from=build --chown=next:next /app/next.config.mjs ./next.config.mjs
USER next
EXPOSE 3000
CMD ["npm", "run", "start"]
