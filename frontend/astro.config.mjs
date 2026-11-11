// @ts-check
import preact from "@astrojs/preact";
import { defineConfig } from "astro/config";

// Web estática: Astro genera HTML en dist/ y Cloudflare Workers lo sirve (ver wrangler.jsonc).
// La interactividad vive solo en islas Preact (encuesta, recomendación, cuenta).
export default defineConfig({
  site: "https://proyectopadel.example", // TODO: dominio definitivo
  output: "static",
  trailingSlash: "always",
  integrations: [preact()],
});
