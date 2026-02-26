FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build
# Output is in /app/dist

FROM scratch AS export
COPY --from=builder /app/dist /dist
