import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { MESSAGE_CATALOG } from '../../messages/message-catalog';
import { MessageCatalogService } from '../../messages/message-catalog.service';
import { PaymentScreenLayoutComponent } from './payment-screen-layout.component';

const componentDir = path.dirname(fileURLToPath(import.meta.url));
const componentSource = readFileSync(path.join(componentDir, 'payment-screen-layout.component.ts'), 'utf-8');

describe('PaymentScreenLayoutComponent', () => {
  it('declara un único punto de contenido principal (un solo <ng-content>)', () => {
    const matches = componentSource.match(/<ng-content/g) ?? [];
    expect(matches.length).toBe(1);
  });

  it('muestra el elemento de ayuda por defecto sin configuración adicional', () => {
    const instance = new PaymentScreenLayoutComponent(new MessageCatalogService());

    expect(instance.showHelp).toBe(true);
    expect(instance.helpMessage).toBe(MESSAGE_CATALOG['ayuda.necesitasAyuda'].text);
  });

  it('permite desactivar explícitamente el elemento de ayuda', () => {
    const instance = new PaymentScreenLayoutComponent(new MessageCatalogService());
    instance.showHelp = false;

    expect(instance.showHelp).toBe(false);
  });

  it('resuelve el texto de ayuda desde el catálogo de mensajes, no hardcodeado', () => {
    expect(componentSource).not.toContain('¿Necesitas ayuda?');
    expect(componentSource).toContain('messageCatalog.get');
  });
});
