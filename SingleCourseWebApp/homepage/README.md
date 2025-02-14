## Getting Started

First, install the dependencies:

```bash
pnpm i
```

Build the project:

```bash
pnpm build
```

Run the development server:

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Docker

Build the Docker image:

```bash
docker build -t homepage .
```

Run the Docker container using docker-compose:

```bash
docker-compose up --build
```

or using make:

```bash
make up
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
