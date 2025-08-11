# frontend/Dockerfile
# --- Dev target: runs Vite dev server ---
FROM node:20 AS dev
WORKDIR /usr/src/app
COPY package.json package-lock.json* ./
RUN npm ci || npm i
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "--port", "5173"]

# --- Prod build ---
FROM node:20 AS build
WORKDIR /usr/src/app
COPY package.json package-lock.json* ./
RUN npm ci || npm i
COPY . .
RUN npm run build

# --- Nginx serve ---
FROM nginx:alpine AS prod
COPY --from=build /usr/src/app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]