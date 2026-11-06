# Proposal

## Why

HU01 (confirmación de pagos de bajo monto) exige que **todas** las pantallas del flujo de pago (S1–S4)
cumplan los mismos requisitos de inclusión (T11 / CA5 — Inclusión y accesibilidad): tamaño de texto y
contraste, botones grandes, íconos siempre con texto, un objetivo por pantalla, ayuda visible, soporte de
lector de pantalla y un estado "En proceso" que no se pierda al cerrar la app. Hoy `web/src/app` solo tiene
`LoginComponent` y `DashboardComponent`, ninguno de los dos construido para el flujo de pago, y ya muestra el
patrón de riesgo que esta HU busca evitar: los mensajes visibles al usuario están hardcodeados en el
componente (`web/src/app/login/login.component.ts:34-57`, p. ej. `'<strong>Ingrese un usuario.</strong>'`) y
no existe ningún componente de UI base reutilizable ni mecanismo de catálogo de textos. Si cada slice S1–S4
reimplementa por su cuenta tamaño de texto, contraste, botones, textos de ayuda y manejo del estado "En
proceso", se duplica lógica y copy y aumenta el riesgo de incumplir el requisito de inclusión en alguna
pantalla. Por eso HU01-S0 se construye primero, como habilitador técnico independiente, antes de S1–S4.

Fuente del trabajo: HU01-S0 — Catálogo de mensajes y componentes de accesibilidad base
(`HU01-S0-catalogo-mensajes.md`), slice derivada de HU01 — Confirmación de pagos de bajo monto. Componente:
`web/`.

## What Changes

- Se introduce un catálogo de mensajes centralizado y editable (el mecanismo, no el copy final) para los
  textos visibles de las pantallas del flujo de pago: saludo, resumen de confirmación, estados terminales,
  ayuda y errores.
- Se introducen componentes de UI base reutilizables para el flujo de pago que garantizan, sin que cada
  pantalla los reimplemente: texto ≥ 18 px y contraste WCAG AA, botones ≥ 48 px, íconos siempre acompañados
  de texto, un objetivo por pantalla con lenguaje simple, un elemento de ayuda visible ("¿Necesitas ayuda?"),
  compatibilidad con lector de pantalla (roles/labels accesibles) y un estado "En proceso" con mensaje
  tranquilizador que se mantiene si el pagador cierra y reabre la app.
- No se modifica `LoginComponent`, `DashboardComponent` ni ningún endpoint consumido por el frontend
  (`/auth/login`, `/api/tasks`): el cambio es aditivo (nuevo catálogo + nuevos componentes compartidos), no
  hay **BREAKING**.
- No se construyen en este cambio las pantallas funcionales del flujo de pago (saludo, confirmación,
  resultados, orquestador): esas corresponden a HU01-S1–S4 y consumirán el catálogo y los componentes
  definidos aquí.

## Capabilities

### New Capabilities

- `payment-ui-message-catalog`: catálogo de mensajes centralizado y editable para los textos visibles de las
  pantallas del flujo de pago, consumido en lugar de strings hardcodeados en cada componente.
- `payment-ui-accessible-components`: componentes de UI base reutilizables que garantizan los requisitos de
  inclusión y accesibilidad (tamaño/contraste, botones, íconos con texto, ayuda visible, lector de pantalla,
  estado "En proceso" resiliente) para cualquier pantalla del flujo de pago construida sobre ellos.

### Modified Capabilities

<!-- Ninguna: openspec/specs/ no contiene specs previas y este cambio no modifica LoginComponent,
     DashboardComponent ni los contratos de /auth/login o /api/tasks. -->

## Impact

- Código afectado: nuevo módulo compartido bajo `web/src/app/` (estructura concreta a definir en
  `design.md`) con el catálogo de mensajes y los componentes de UI base; `LoginComponent`,
  `DashboardComponent` y el resto de `web/src/app` quedan sin cambios.
- APIs: ninguna; es una capa de UI/contenido front-end, sin interacción con `/auth/login` ni `/api/tasks`.
- Dependencias: ninguna nueva prevista (a confirmar en `design.md` si se requiere tooling adicional de
  pruebas de accesibilidad).
- Verificación: pruebas unitarias/de componente sobre la resolución del catálogo y el contrato de los
  componentes base (tamaño, contraste, roles ARIA), ejecutadas con el comando de pruebas de `web/` (ver
  `python tools/lab.py test web` desde la raíz); meta de cobertura del código modificado ≥ 85%.
- Dependientes: este cambio es prerrequisito de HU01-S1, HU01-S2, HU01-S3 y HU01-S4 (no se implementan en
  este cambio).
