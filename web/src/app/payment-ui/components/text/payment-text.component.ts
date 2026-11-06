import { Component, Input } from '@angular/core';
import { meetsWcagAaContrast } from '../../color-contrast';

/** Tamaño mínimo de texto exigido por HU01-S0 (CA5 — Inclusión y accesibilidad). */
export const PAYMENT_TEXT_MIN_FONT_SIZE_PX = 18;
export const PAYMENT_TEXT_FOREGROUND_COLOR = '#1a1a1a';
export const PAYMENT_TEXT_BACKGROUND_COLOR = '#ffffff';

/**
 * Componente de texto base del flujo de pago: garantiza tamaño mínimo y contraste
 * WCAG AA vía su propio CSS, para que ninguna pantalla consumidora deba
 * reimplementar esa lógica (ver specs/payment-ui-accessible-components).
 */
@Component({
  selector: 'app-payment-text',
  standalone: true,
  template: `<span class="payment-text" [attr.role]="role"><ng-content></ng-content></span>`,
  styleUrl: './payment-text.component.css'
})
export class PaymentTextComponent {
  /** Rol ARIA opcional (por ejemplo, "status" para un mensaje de estado). */
  @Input() role: string | null = null;

  readonly minFontSizePx = PAYMENT_TEXT_MIN_FONT_SIZE_PX;
  readonly meetsContrastRequirement = meetsWcagAaContrast(
    PAYMENT_TEXT_FOREGROUND_COLOR,
    PAYMENT_TEXT_BACKGROUND_COLOR
  );
}
