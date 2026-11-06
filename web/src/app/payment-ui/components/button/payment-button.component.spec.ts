import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { PAYMENT_BUTTON_MIN_TOUCH_TARGET_PX, PaymentButtonComponent } from './payment-button.component';

const componentDir = path.dirname(fileURLToPath(import.meta.url));
const css = readFileSync(path.join(componentDir, 'payment-button.component.css'), 'utf-8');
const componentSource = readFileSync(path.join(componentDir, 'payment-button.component.ts'), 'utf-8');

describe('PaymentButtonComponent', () => {
  it('exige un área táctil mínima de 48px, reflejada en su propia hoja de estilos', () => {
    expect(PAYMENT_BUTTON_MIN_TOUCH_TARGET_PX).toBeGreaterThanOrEqual(48);
    expect(css).toMatch(/min-width:\s*48px/);
    expect(css).toMatch(/min-height:\s*48px/);
  });

  it('declara un <button> nativo con aria-label configurable en su plantilla', () => {
    expect(componentSource).toMatch(/<button[^>]*\[attr\.aria-label\]="ariaLabel"/);

    const instance = new PaymentButtonComponent();
    instance.ariaLabel = 'Confirmar pago';
    expect(instance.ariaLabel).toBe('Confirmar pago');
  });

  it('permite deshabilitar el botón durante el procesamiento', () => {
    const instance = new PaymentButtonComponent();

    expect(instance.disabled).toBe(false);
    instance.disabled = true;
    expect(instance.disabled).toBe(true);
  });
});
