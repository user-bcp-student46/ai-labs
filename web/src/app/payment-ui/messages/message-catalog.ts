/**
 * Catálogo editable de mensajes visibles al pagador en el flujo de pago (HU01-S0).
 *
 * El contenido de `MESSAGE_CATALOG` es la configuración editable: cambiar un texto
 * aquí no requiere tocar `message-catalog.service.ts` ni ningún componente consumidor
 * (ver openspec/changes/hu01-s0-catalogo-mensajes/specs/payment-ui-message-catalog).
 *
 * Nota: las etiquetas de texto son provisionales. El copy final de los estados
 * terminales y del resto del catálogo queda pendiente de cierre con producto
 * (ver HU01-S0-catalogo-mensajes.md — Preguntas abiertas).
 */

export type MessageCategory = 'saludo' | 'confirmacion' | 'estado' | 'ayuda' | 'error';

export interface MessageCatalogEntry {
  readonly category: MessageCategory;
  readonly text: string;
}

export type MessageCatalog = Readonly<Record<string, MessageCatalogEntry>>;

/** Clave del mensaje tranquilizador del estado "En proceso" (ver componente ProcessingState). */
export const PROCESSING_STATE_MESSAGE_KEY = 'estado.enProceso';

export const MESSAGE_CATALOG: MessageCatalog = {
  'saludo.bienvenida': {
    category: 'saludo',
    text: 'Hola, vamos a confirmar tu pago.'
  },
  'confirmacion.resumen': {
    category: 'confirmacion',
    text: 'Revisa los datos antes de confirmar tu pago.'
  },
  'estado.exitoso': {
    category: 'estado',
    text: 'Tu pago se realizó con éxito.'
  },
  'estado.fallido': {
    category: 'estado',
    text: 'No pudimos completar tu pago.'
  },
  'estado.expirado': {
    category: 'estado',
    text: 'Tu pago tardó más de lo esperado y no se pudo confirmar.'
  },
  [PROCESSING_STATE_MESSAGE_KEY]: {
    category: 'estado',
    text: 'Estamos procesando tu pago. No cierres la aplicación, tu intento no se perderá.'
  },
  'ayuda.necesitasAyuda': {
    category: 'ayuda',
    text: '¿Necesitas ayuda?'
  },
  'error.generico': {
    category: 'error',
    text: 'Ocurrió un problema y no pudimos continuar. Intenta nuevamente.'
  },
  'error.saldoInsuficiente': {
    category: 'error',
    text: 'No cuentas con saldo suficiente para este pago.'
  }
};

/** Prefijo de los mensajes devueltos para una clave sin entrada configurada. */
export const UNCONFIGURED_MESSAGE_PREFIX = '[mensaje no configurado';

/**
 * Resuelve el texto de una clave contra un catálogo dado. Nunca lanza una excepción:
 * una clave sin entrada configurada devuelve un resultado identificable para que la
 * ausencia de copy sea detectable antes de llegar a producción.
 */
export function resolveMessage(catalog: MessageCatalog, key: string): string {
  const entry = catalog[key];
  return entry ? entry.text : `${UNCONFIGURED_MESSAGE_PREFIX}: ${key}]`;
}

/** Lista las claves del catálogo que pertenecen a una categoría dada. */
export function listKeysByCategory(catalog: MessageCatalog, category: MessageCategory): string[] {
  return Object.entries(catalog)
    .filter(([, entry]) => entry.category === category)
    .map(([key]) => key);
}
