FROM node:18-alpine

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

COPY package.json ./

RUN pnpm install

COPY . .

RUN pnpm run build

CMD ["pnpm", "run", "dev"]
