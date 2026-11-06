import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { PaymentIconTextComponent } from './payment-icon-text.component';

const componentDir = path.dirname(fileURLToPath(import.meta.url));
const componentSource = readFileSync(path.join(componentDir, 'payment-icon-text.component.ts'), 'utf-8');

describe('PaymentIconTextComponent', () => {
  it('no permite renderizarse sin un texto visible asociado al ícono', () => {
    const instance = new PaymentIconTextComponent();

    expect(instance.canRender).toBe(false);

    instance.text = '   ';
    expect(instance.canRender).toBe(false);
  });

  it('se renderiza cuando se provee un texto', () => {
    const instance = new PaymentIconTextComponent();
    instance.icon = '⚠';
    instance.text = 'Saldo insuficiente';

    expect(instance.canRender).toBe(true);
  });

  it('marca el ícono como aria-hidden para que solo el texto sea anunciado', () => {
    expect(componentSource).toMatch(/aria-hidden="true"[^>]*>\{\{\s*icon\s*\}\}/);
  });

  it('no declara ninguna variante de "solo ícono" en su plantilla', () => {
    expect(componentSource).not.toMatch(/icon-only/i);
    expect(componentSource).toContain('@if (canRender)');
  });
});
