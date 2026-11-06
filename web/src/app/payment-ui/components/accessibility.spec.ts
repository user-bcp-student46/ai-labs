import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * Verificación transversal (tarea 3.6): confirma que los cinco componentes base
 * de `payment-ui` exponen roles y/o etiquetas accesibles en su plantilla, para
 * que un lector de pantalla pueda anunciarlos correctamente (ver
 * specs/payment-ui-accessible-components — Compatibilidad con lector de
 * pantalla). Cada componente ya tiene, además, su propia prueba dedicada a este
 * punto; esta suite solo confirma la cobertura conjunta de los cinco.
 */

const componentsDir = path.dirname(fileURLToPath(import.meta.url));

function readComponentSource(relativePath: string): string {
  return readFileSync(path.join(componentsDir, relativePath), 'utf-8');
}

describe('Compatibilidad con lector de pantalla de los componentes base', () => {
  it('texto: expone un rol ARIA configurable', () => {
    const source = readComponentSource('text/payment-text.component.ts');
    expect(source).toMatch(/\[attr\.role\]="role"/);
  });

  it('botón: expone una etiqueta accesible (aria-label) sobre un elemento nativo', () => {
    const source = readComponentSource('button/payment-button.component.ts');
    expect(source).toMatch(/<button[^>]*\[attr\.aria-label\]="ariaLabel"/);
  });

  it('ícono+texto: marca el ícono decorativo como aria-hidden y mantiene el texto anunciable', () => {
    const source = readComponentSource('icon-text/payment-icon-text.component.ts');
    expect(source).toMatch(/aria-hidden="true"/);
    expect(source).toContain('payment-icon-text__label');
  });

  it('layout de pantalla: marca el elemento de ayuda con un rol anunciable', () => {
    const source = readComponentSource('screen-layout/payment-screen-layout.component.ts');
    expect(source).toMatch(/role="note"/);
  });

  it('estado "En proceso": expone un rol de estado con anuncio en vivo', () => {
    const source = readComponentSource('processing-state/payment-processing-state.component.ts');
    expect(source).toMatch(/role="status"/);
    expect(source).toMatch(/aria-live="polite"/);
  });
});
