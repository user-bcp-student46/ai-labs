import { Injectable } from '@angular/core';
import { MESSAGE_CATALOG, MessageCategory, listKeysByCategory, resolveMessage } from './message-catalog';

/**
 * Servicio inyectable que resuelve texto visible al pagador desde el catálogo
 * centralizado (`message-catalog.ts`). Las pantallas del flujo de pago deben
 * obtener su copy a través de este servicio en vez de escribirlo literal en el
 * componente.
 */
@Injectable({ providedIn: 'root' })
export class MessageCatalogService {
  get(key: string): string {
    return resolveMessage(MESSAGE_CATALOG, key);
  }

  keysByCategory(category: MessageCategory): string[] {
    return listKeysByCategory(MESSAGE_CATALOG, category);
  }
}
