FROM node:16.16.0-slim

WORKDIR /app

COPY package*.json /app/

RUN npm install --legacy-peer-deps

COPY . /app/

CMD ["./node_modules/.bin/parcel", "watch", "bundles-src/index.js", "--dist-dir", "bundles", "--public-url=./"]