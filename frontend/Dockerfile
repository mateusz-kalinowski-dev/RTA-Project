# Etap 1: Budowanie aplikacji
FROM node:20 AS build
WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

RUN npm run build

# Etap 2: Serwowanie przez nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
