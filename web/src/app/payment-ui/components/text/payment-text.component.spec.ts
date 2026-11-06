import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { meetsWcagAaContrast } from '../../color-contrast';
import {
  PAYMENT_TEXT_BACKGROUND_COLOR,
  PAYMENT_TEXT_FOREGROUND_COLOR,
  PAYMENT_TEXT_MIN_FONT_SIZE_PX,
  PaymentTextComponent
} from './payment-text.component';

const cssPath = path.join(path.dirname(fileURLToPath(import.meta.url)), 'payment-text.component.css');
const css = readFileSync(cssPath, 'utf-8');

describe('PaymentTextComponent', () => {
  it('exige un tamaño de texto mínimo de 18px, reflejado en su propia hoja de estilos', () => {
    expect(PAYMENT_TEXT_MIN_FONT_SIZE_PX).toBeGreaterThanOrEqual(18);
    expect(css).toMatch(/font-size:\s*18px/);
  });

  it('exige un contraste conforme a WCAG AA entre su texto y su fondo', () => {
    expect(meetsWcagAaContrast(PAYMENT_TEXT_FOREGROUND_COLOR, PAYMENT_TEXT_BACKGROUND_COLOR)).toBe(true);
    expect(css).toContain(PAYMENT_TEXT_FOREGROUND_COLOR);
    expect(css).toContain(PAYMENT_TEXT_BACKGROUND_COLOR);
  });

  it('expone el tamaño y el contraste garantizados sin que la pantalla consumidora los declare', () => {
    const instance = new PaymentTextComponent();

    expect(instance.minFontSizePx).toBe(18);
    expect(instance.meetsContrastRequirement).toBe(true);
  });
});
