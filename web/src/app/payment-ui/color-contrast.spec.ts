import { describe, expect, it } from 'vitest';
import { WCAG_AA_NORMAL_TEXT_MIN_CONTRAST, contrastRatio, meetsWcagAaContrast } from './color-contrast';

describe('contrastRatio', () => {
  it('calcula 21:1 para negro sobre blanco (contraste máximo)', () => {
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 0);
  });

  it('es simétrica respecto al orden de los colores', () => {
    expect(contrastRatio('#1a1a1a', '#ffffff')).toBeCloseTo(contrastRatio('#ffffff', '#1a1a1a'), 5);
  });

  it('admite la notación hexadecimal abreviada de 3 dígitos', () => {
    expect(contrastRatio('#000', '#fff')).toBeCloseTo(contrastRatio('#000000', '#ffffff'), 5);
  });
});

describe('meetsWcagAaContrast', () => {
  it('acepta un par de colores que supera el mínimo AA de 4.5:1', () => {
    expect(contrastRatio('#1a1a1a', '#ffffff')).toBeGreaterThanOrEqual(WCAG_AA_NORMAL_TEXT_MIN_CONTRAST);
    expect(meetsWcagAaContrast('#1a1a1a', '#ffffff')).toBe(true);
  });

  it('rechaza un par de colores de bajo contraste', () => {
    expect(meetsWcagAaContrast('#fefefe', '#ffffff')).toBe(false);
  });
});
