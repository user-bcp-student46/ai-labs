/**
 * Persistencia del estado "En proceso" en almacenamiento local del navegador.
 *
 * La clave de almacenamiento se centraliza aquí (contrato de agentes de `web`,
 * regla 12: sin valores "mágicos" de `localStorage` sueltos en el código) y la
 * lógica de lectura/escritura se expone como funciones puras sobre una interfaz
 * mínima de almacenamiento, para poder probarla sin depender de un DOM real.
 */

/** Clave de `localStorage` que indica si un intento de pago sigue "en curso". */
export const PAYMENT_PROCESSING_STORAGE_KEY = 'workshop_payment_processing_active';

const ACTIVE_VALUE = 'true';

/** Subconjunto de la Web Storage API que esta persistencia necesita. */
export interface KeyValueStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

/** Indica si, según el almacenamiento dado, el estado "En proceso" sigue activo. */
export function readProcessingFlag(storage: KeyValueStorage): boolean {
  return storage.getItem(PAYMENT_PROCESSING_STORAGE_KEY) === ACTIVE_VALUE;
}

/** Activa o desactiva la bandera de "En proceso" en el almacenamiento dado. */
export function writeProcessingFlag(storage: KeyValueStorage, active: boolean): void {
  if (active) {
    storage.setItem(PAYMENT_PROCESSING_STORAGE_KEY, ACTIVE_VALUE);
  } else {
    storage.removeItem(PAYMENT_PROCESSING_STORAGE_KEY);
  }
}
