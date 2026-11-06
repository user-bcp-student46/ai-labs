import { Component, Input } from '@angular/core';

/**
 * Componente de ícono+texto base del flujo de pago: nunca admite un modo "solo
 * ícono" — si no se provee un texto, no se renderiza nada (ver
 * specs/payment-ui-accessible-components — Íconos siempre acompañados de texto).
 */
@Component({
  selector: 'app-payment-icon-text',
  standalone: true,
  template: `
    @if (canRender) {
      <span class="payment-icon-text">
        <span class="payment-icon-text__icon" aria-hidden="true">{{ icon }}</span>
        <span class="payment-icon-text__label">{{ text }}</span>
      </span>
    }
  `,
  styleUrl: './payment-icon-text.component.css'
})
export class PaymentIconTextComponent {
  @Input() icon = '';
  @Input() text = '';

  /** Solo se renderiza si hay un texto visible asociado al ícono. */
  get canRender(): boolean {
    return this.text.trim().length > 0;
  }
}
