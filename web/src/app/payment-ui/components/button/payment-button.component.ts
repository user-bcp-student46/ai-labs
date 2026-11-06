import { Component, Input } from '@angular/core';

/** Área táctil mínima exigida por HU01-S0 (CA5 — Inclusión y accesibilidad). */
export const PAYMENT_BUTTON_MIN_TOUCH_TARGET_PX = 48;

/**
 * Componente de botón base del flujo de pago: garantiza un área táctil mínima y
 * expone una etiqueta accesible, para que ninguna pantalla consumidora deba
 * reimplementar esa lógica (ver specs/payment-ui-accessible-components).
 */
@Component({
  selector: 'app-payment-button',
  standalone: true,
  template: `
    <button
      type="button"
      class="payment-button"
      [attr.aria-label]="ariaLabel"
      [disabled]="disabled"
    >
      <ng-content></ng-content>
    </button>
  `,
  styleUrl: './payment-button.component.css'
})
export class PaymentButtonComponent {
  /** Etiqueta accesible anunciada por el lector de pantalla. */
  @Input() ariaLabel: string | null = null;
  @Input() disabled = false;

  readonly minTouchTargetPx = PAYMENT_BUTTON_MIN_TOUCH_TARGET_PX;
}
