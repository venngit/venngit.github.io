FROM node:18-alpine

WORKDIR /usr/src/app

COPY package.json ./
COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
EXPOSE 3000
CMD ["node", "server.js"]
