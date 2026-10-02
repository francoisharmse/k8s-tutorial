# ---- build stage: compile the Vite/React app to static assets ----
FROM node:20-alpine AS build
WORKDIR /ui
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- serve stage: nginx hosts dist/ and proxies /api ----
# nginx.conf is NOT baked in — the nginx-conf ConfigMap mounts it,
# so config changes roll out without a rebuild (step 3.2).
FROM nginx:alpine
COPY --from=build /ui/dist /usr/share/nginx/html
EXPOSE 80
