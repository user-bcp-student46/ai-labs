import { Component, Input } from '@angular/core';
import { MessageCatalogService } from '../../messages/message-catalog.service';

const HELP_MESSAGE_KEY = 'ayuda.necesitasAyuda';

/**
 * Layout base de pantalla del flujo de pago: estructura el contenido alrededor de
 * un único punto de contenido principal y muestra, por defecto y sin
 * configuración adicional, un elemento de ayuda visible (ver
 * specs/payment-ui-accessible-components).
 */
@Component({
  selector: 'app-payment-screen-layout',
  standalone: true,
  template: `
    <div class="payment-screen-layout">
      <main class="payment-screen-layout__main">
        <ng-content></ng-content>
      </main>
      @if (showHelp) {
        <p class="payment-screen-layout__help" role="note">{{ helpMessage }}</p>
      }
    </div>
  `,
  styleUrl: './payment-screen-layout.component.css'
})
export class PaymentScreenLayoutComponent {
  /** El elemento de ayuda se muestra por defecto; solo se oculta si se desactiva explícitamente. */
  @Input() showHelp = true;

  constructor(private readonly messageCatalog: MessageCatalogService) {}

  get helpMessage(): string {
    return this.messageCatalog.get(HELP_MESSAGE_KEY);
  }
}
