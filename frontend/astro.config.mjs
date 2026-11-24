// @ts-check
import preact from "@astrojs/preact";
import { defineConfig } from "astro/config";
import { loadEnv } from "vite";

// Web estática: Astro genera HTML en dist/ y cualquier alojamiento estático lo sirve
// (Vercel con el vercel.json de la raíz del repositorio; wrangler.jsonc queda de la configuración anterior en Cloudflare).
// La interactividad vive solo en islas Preact (cuestionario, recomendación, cuenta).

/**
 * Dominio público, usado en las URL canónicas y de Open Graph.
 * 1. SITE_URL si se define (dominio propio, p. ej. https://palaideal.es).
 * 2. En Vercel, el dominio de producción del proyecto (también en las previews,
 *    para que las canónicas apunten siempre a producción).
 * 3. En local, el servidor de desarrollo.
 */
// loadEnv junta las variables del entorno (las de Vercel) y las de frontend/.env.
const env = loadEnv("", ".", "");
const sitio =
  env.SITE_URL?.trim() ||
  (env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${env.VERCEL_PROJECT_PRODUCTION_URL}` : "http://localhost:4321");

export default defineConfig({
  site: sitio,
  output: "static",
  trailingSlash: "always",
  integrations: [preact()],
});
