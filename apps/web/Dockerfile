# 构建阶段：Vite 生产构建
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# 运行阶段：nginx 托管静态产物，/api 反代到 api 容器
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/40-local-dev-token.sh /docker-entrypoint.d/40-local-dev-token.sh
RUN chmod +x /docker-entrypoint.d/40-local-dev-token.sh
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
