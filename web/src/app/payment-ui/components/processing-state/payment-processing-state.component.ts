import { Component, OnInit } from '@angular/core';
import { MessageCatalogService } from '../../messages/message-catalog.service';
import { PROCESSING_STATE_MESSAGE_KEY } from '../../messages/message-catalog';
import { PAYMENT_PROCESSING_STORAGE_KEY, readProcessingFlag, writeProcessingFlag } from './processing-state-storage';

/**
 * Componente base de estado "En proceso" del flujo de pago: muestra el mensaje
 * tranquilizador del catálogo y persiste su bandera de "en curso" en
 * `localStorage`, de modo que el mensaje se vuelve a mostrar si el pagador
 * cierra y reabre la app mientras el intento sigue vigente (ver
 * specs/payment-ui-accessible-components — Estado "En proceso" resiliente).
 *
 * Nota de alcance: solo persiste la indicación visual; la persistencia real del
 * intento de pago depende de la integración de HU01-S1.
 */
@Component({
  selector: 'app-payment-processing-state',
  standalone: true,
  template: `
    @if (isActive) {
      <p class="payment-processing-state" role="status" aria-live="polite">{{ message }}</p>
    }
  `,
  styleUrl: './payment-processing-state.component.css'
})
export class PaymentProcessingStateComponent implements OnInit {
  isActive = false;

  constructor(private readonly messageCatalog: MessageCatalogService) {}

  get message(): string {
    return this.messageCatalog.get(PROCESSING_STATE_MESSAGE_KEY);
  }

  ngOnInit(): void {
    this.isActive = readProcessingFlag(localStorage);
  }

  /** Marca el estado "En proceso" como activo y lo persiste para que sobreviva a un cierre de la app. */
  start(): void {
    this.isActive = true;
    writeProcessingFlag(localStorage, true);
  }

  /** Limpia el estado "En proceso" al alcanzar un resultado terminal (Exitoso/Fallido/Expirado). */
  stop(): void {
    this.isActive = false;
    writeProcessingFlag(localStorage, false);
  }
}

export { PAYMENT_PROCESSING_STORAGE_KEY };
