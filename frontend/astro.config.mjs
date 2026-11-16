// @ts-check
import preact from "@astrojs/preact";
import { defineConfig } from "astro/config";

// Web estática: Astro genera HTML en dist/ y cualquier alojamiento estático lo sirve
// (Vercel con vercel.json; wrangler.jsonc queda de la configuración anterior en Cloudflare).
// La interactividad vive solo en islas Preact (cuestionario, recomendación, cuenta).
export default defineConfig({
  site: "https://proyectopadel.example", // TODO: dominio definitivo
  output: "static",
  trailingSlash: "always",
  integrations: [preact()],
});
