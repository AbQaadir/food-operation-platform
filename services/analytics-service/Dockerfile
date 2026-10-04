FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist ./dist
USER node
EXPOSE 8086
CMD ["node", "dist/index.js"]
