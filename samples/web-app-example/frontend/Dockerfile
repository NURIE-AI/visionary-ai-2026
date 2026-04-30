# build stage
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Optional: bake personal API key / base into the static build (same as .env at build time).
ARG VITE_NURIE_API_KEY
ARG VITE_NURIE_API_BASE
ENV VITE_NURIE_API_KEY=$VITE_NURIE_API_KEY
ENV VITE_NURIE_API_BASE=$VITE_NURIE_API_BASE
RUN npm run build

# production stage
FROM nginx:stable-alpine as production-stage
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
