import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { MESSAGE_CATALOG, PROCESSING_STATE_MESSAGE_KEY } from '../../messages/message-catalog';
import { MessageCatalogService } from '../../messages/message-catalog.service';
import { PaymentProcessingStateComponent } from './payment-processing-state.component';
import { PAYMENT_PROCESSING_STORAGE_KEY } from './processing-state-storage';

const componentDir = path.dirname(fileURLToPath(import.meta.url));
const componentSource = readFileSync(path.join(componentDir, 'payment-processing-state.component.ts'), 'utf-8');

/**
 * `localStorage` no existe en el entorno Node usado por vitest (ver
 * `web/vitest.config.ts` — `environment: 'node'`). Se sustituye por un
 * almacenamiento en memoria equivalente, solo para esta suite, para poder
 * ejercitar la persistencia real que usa el componente en el navegador.
 */
function installFakeLocalStorage(): Storage {
  const store = new Map<string, string>();
  const fake = {
    getItem: (key: string) => (store.has(key) ? store.get(key)! : null),
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => store.clear(),
    key: () => null,
    get length() {
      return store.size;
    }
  } as Storage;
  (globalThis as { localStorage?: Storage }).localStorage = fake;
  return fake;
}

describe('PaymentProcessingStateComponent', () => {
  beforeEach(() => {
    installFakeLocalStorage();
  });

  afterEach(() => {
    delete (globalThis as { localStorage?: Storage }).localStorage;
  });

  it('no está activo al inicializarse si no hay un intento persistido', () => {
    const instance = new PaymentProcessingStateComponent(new MessageCatalogService());
    instance.ngOnInit();

    expect(instance.isActive).toBe(false);
  });

  it('persiste el estado activo y lo recupera tras simular una recarga (nueva instancia)', () => {
    const first = new PaymentProcessingStateComponent(new MessageCatalogService());
    first.ngOnInit();
    first.start();

    expect(localStorage.getItem(PAYMENT_PROCESSING_STORAGE_KEY)).not.toBeNull();

    // Simula cerrar y reabrir la app: una nueva instancia lee el mismo almacenamiento.
    const second = new PaymentProcessingStateComponent(new MessageCatalogService());
    second.ngOnInit();

    expect(second.isActive).toBe(true);
    expect(second.message).toBe(MESSAGE_CATALOG[PROCESSING_STATE_MESSAGE_KEY].text);
  });

  it('limpia el estado persistido al detenerse (resultado terminal alcanzado)', () => {
    const instance = new PaymentProcessingStateComponent(new MessageCatalogService());
    instance.ngOnInit();
    instance.start();
    instance.stop();

    expect(instance.isActive).toBe(false);
    expect(localStorage.getItem(PAYMENT_PROCESSING_STORAGE_KEY)).toBeNull();
  });

  it('resuelve su mensaje desde el catálogo de mensajes, no hardcodeado', () => {
    expect(componentSource).not.toContain('Estamos procesando tu pago');
    expect(componentSource).toContain('messageCatalog.get');
  });

  it('expone un rol de estado anunciable por un lector de pantalla', () => {
    expect(componentSource).toMatch(/role="status"/);
    expect(componentSource).toMatch(/aria-live="polite"/);
  });
});
