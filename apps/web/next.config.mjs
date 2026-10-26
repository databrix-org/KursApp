import path from "node:path";
import { fileURLToPath } from "node:url";
const root = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../..",
);
const config = {
  output: "standalone",
  outputFileTracingRoot: root,
  transpilePackages: ["@repo/design-system", "@repo/api-client", "@repo/i18n"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/:path*`,
      },
      {
        source: "/auth/:path*",
        destination: `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/auth/:path*`,
      },
    ];
  },
};

export default config;
