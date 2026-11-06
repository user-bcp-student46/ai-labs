import { describe, expect, it } from 'vitest';
import {
  MESSAGE_CATALOG,
  PROCESSING_STATE_MESSAGE_KEY,
  UNCONFIGURED_MESSAGE_PREFIX,
  listKeysByCategory,
  resolveMessage
} from './message-catalog';
import { MessageCatalogService } from './message-catalog.service';

const CATEGORIES = ['saludo', 'confirmacion', 'estado', 'ayuda', 'error'] as const;

describe('resolveMessage', () => {
  it('resuelve al menos una clave real por cada categoría del catálogo', () => {
    for (const category of CATEGORIES) {
      const keys = listKeysByCategory(MESSAGE_CATALOG, category);
      expect(keys.length).toBeGreaterThan(0);
      const [firstKey] = keys;
      expect(resolveMessage(MESSAGE_CATALOG, firstKey)).toBe(MESSAGE_CATALOG[firstKey].text);
    }
  });

  it('devuelve un resultado identificable para una clave no configurada, sin lanzar una excepción', () => {
    expect(() => resolveMessage(MESSAGE_CATALOG, 'categoria.inexistente')).not.toThrow();
    const result = resolveMessage(MESSAGE_CATALOG, 'categoria.inexistente');
    expect(result).toContain(UNCONFIGURED_MESSAGE_PREFIX);
    expect(result.length).toBeGreaterThan(0);
  });

  it('refleja un texto editado sin cambiar la función de resolución ni el servicio', () => {
    const catalogWithEditedText = {
      ...MESSAGE_CATALOG,
      'estado.exitoso': { category: 'estado' as const, text: 'Nuevo texto editado' }
    };

    expect(resolveMessage(catalogWithEditedText, 'estado.exitoso')).toBe('Nuevo texto editado');
    // El catálogo original no se modifica: demuestra que el cambio vive en la
    // configuración, no en el código de `resolveMessage`.
    expect(resolveMessage(MESSAGE_CATALOG, 'estado.exitoso')).toBe(MESSAGE_CATALOG['estado.exitoso'].text);
  });

  it('incluye la clave del mensaje tranquilizador de "En proceso" usada por el componente de ese estado', () => {
    expect(MESSAGE_CATALOG[PROCESSING_STATE_MESSAGE_KEY]).toBeDefined();
    expect(MESSAGE_CATALOG[PROCESSING_STATE_MESSAGE_KEY].text.length).toBeGreaterThan(0);
  });
});

describe('MessageCatalogService', () => {
  it('delega la resolución de claves en el catálogo configurado', () => {
    const service = new MessageCatalogService();

    expect(service.get('ayuda.necesitasAyuda')).toBe(MESSAGE_CATALOG['ayuda.necesitasAyuda'].text);
    expect(service.get('clave.inexistente')).toContain(UNCONFIGURED_MESSAGE_PREFIX);
  });

  it('expone las claves de una categoría', () => {
    const service = new MessageCatalogService();

    const errorKeys = service.keysByCategory('error');
    expect(errorKeys).toContain('error.saldoInsuficiente');
  });
});
