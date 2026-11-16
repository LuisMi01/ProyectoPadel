/** Hooks compartidos por las islas. */
import { useEffect, useState } from "preact/hooks";

import { type EstadoSesion, comprobarSesion, sesionRecordada, suscribir } from "@/lib/cuenta";

/**
 * Lee algo guardado en el navegador y se mantiene al día cuando cambia.
 * `inicial` es lo que se pinta en el servidor y antes de leer el almacenamiento.
 */
export function useGuardado<T>(leer: () => T, inicial: T): T {
  const [valor, setValor] = useState(inicial);
  useEffect(() => {
    const actualizar = () => setValor(leer());
    actualizar();
    return suscribir(actualizar);
    // `leer` se recrea en cada pintado; solo interesa suscribirse una vez.
  }, []);
  return valor;
}

/** true cuando ya se ha leído el almacenamiento (evita parpadeos de «vacío»). */
export function useMontado(): boolean {
  const [montado, setMontado] = useState(false);
  useEffect(() => setMontado(true), []);
  return montado;
}

/** Estado de la sesión: primero lo recordado, luego lo que diga la API. */
export function useSesion(): EstadoSesion | null {
  const [estado, setEstado] = useState<EstadoSesion | null>(null);
  useEffect(() => {
    let vigente = true;
    const recordada = sesionRecordada();
    if (recordada) setEstado({ tipo: "activa", sesion: recordada });
    comprobarSesion().then((e) => vigente && setEstado(e));
    return () => {
      vigente = false;
    };
  }, []);
  return estado;
}
