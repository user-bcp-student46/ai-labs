import { describe, expect, it } from 'vitest';
import {
  KeyValueStorage,
  PAYMENT_PROCESSING_STORAGE_KEY,
  readProcessingFlag,
  writeProcessingFlag
} from './processing-state-storage';

function createFakeStorage(): KeyValueStorage {
  const store = new Map<string, string>();
  return {
    getItem: (key) => (store.has(key) ? store.get(key)! : null),
    setItem: (key, value) => {
      store.set(key, value);
    },
    removeItem: (key) => {
      store.delete(key);
    }
  };
}

describe('processing-state-storage', () => {
  it('no reporta el estado activo cuando nunca se escribió la bandera', () => {
    const storage = createFakeStorage();

    expect(readProcessingFlag(storage)).toBe(false);
  });

  it('persiste la bandera activa y la mantiene disponible para una lectura posterior (simula recarga)', () => {
    const storage = createFakeStorage();

    writeProcessingFlag(storage, true);
    // Una segunda lectura sobre el mismo almacenamiento simula reabrir la app.
    expect(readProcessingFlag(storage)).toBe(true);
    expect(storage.getItem(PAYMENT_PROCESSING_STORAGE_KEY)).not.toBeNull();
  });

  it('limpia la bandera al desactivarla', () => {
    const storage = createFakeStorage();

    writeProcessingFlag(storage, true);
    writeProcessingFlag(storage, false);

    expect(readProcessingFlag(storage)).toBe(false);
    expect(storage.getItem(PAYMENT_PROCESSING_STORAGE_KEY)).toBeNull();
  });
});
