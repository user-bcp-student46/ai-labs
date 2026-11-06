/**
 * Utilidades de contraste de color (WCAG) reutilizadas por los componentes base de
 * `payment-ui` para verificar, en tiempo de ejecución y en pruebas, que el par de
 * colores usado cumple el nivel AA sin duplicar la fórmula en cada componente.
 */

function hexToRgbChannels(hex: string): [number, number, number] {
  const normalized = hex.replace('#', '');
  const expanded =
    normalized.length === 3
      ? normalized
          .split('')
          .map((channel) => channel + channel)
          .join('')
      : normalized;
  const value = parseInt(expanded, 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function channelToLinear(channel: number): number {
  const srgb = channel / 255;
  return srgb <= 0.03928 ? srgb / 12.92 : Math.pow((srgb + 0.055) / 1.055, 2.4);
}

/** Luminancia relativa de un color hexadecimal, según la fórmula WCAG 2.x. */
export function relativeLuminance(hex: string): number {
  const [r, g, b] = hexToRgbChannels(hex).map(channelToLinear);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** Razón de contraste entre dos colores hexadecimales (1 a 21). */
export function contrastRatio(hexA: string, hexB: string): number {
  const luminanceA = relativeLuminance(hexA);
  const luminanceB = relativeLuminance(hexB);
  const lighter = Math.max(luminanceA, luminanceB);
  const darker = Math.min(luminanceA, luminanceB);
  return (lighter + 0.05) / (darker + 0.05);
}

/** Razón de contraste mínima exigida por WCAG 2.x nivel AA para texto normal. */
export const WCAG_AA_NORMAL_TEXT_MIN_CONTRAST = 4.5;

/** Indica si el par de colores cumple el contraste mínimo de WCAG AA para texto normal. */
export function meetsWcagAaContrast(hexA: string, hexB: string): boolean {
  return contrastRatio(hexA, hexB) >= WCAG_AA_NORMAL_TEXT_MIN_CONTRAST;
}
