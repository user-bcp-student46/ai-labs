# Spec Delta

## Purpose

Provee un conjunto de componentes de UI base reutilizables que garantizan automáticamente los requisitos de
inclusión y accesibilidad del flujo de pago, para que ninguna pantalla individual deba reimplementar esa
lógica.

## ADDED Requirements

### Requirement: Tamaño de texto y contraste garantizados

Toda pantalla del flujo de pago construida sobre los componentes de texto base provistos por esta slice
SHALL renderizar el texto con un tamaño mínimo de 18 px y un contraste que cumpla WCAG AA, sin que la
pantalla implemente esa lógica por separado.

#### Scenario: Pantalla usa el componente de texto base

- **WHEN** una pantalla del flujo de pago renderiza un texto usando el componente de texto base
- **THEN** el texto se muestra con tamaño ≥ 18 px y contraste conforme a WCAG AA, sin estilos de tamaño o
  contraste definidos en la propia pantalla

### Requirement: Botones de tamaño accesible

Todo botón interactivo del flujo de pago construido sobre el componente de botón base provisto por esta
slice SHALL tener un área táctil mínima de 48 px.

#### Scenario: Pantalla usa el componente de botón base

- **WHEN** una pantalla del flujo de pago renderiza una acción interactiva usando el componente de botón base
- **THEN** el botón resultante tiene un área táctil ≥ 48 px

### Requirement: Íconos siempre acompañados de texto

Ningún ícono mostrado a través de los componentes base del flujo de pago SHALL presentarse sin un texto
visible que explique su significado.

#### Scenario: Componente de ícono base se usa en una pantalla

- **WHEN** una pantalla del flujo de pago muestra un ícono usando el componente de ícono base
- **THEN** el ícono se renderiza junto con un texto visible asociado, y el componente no admite un modo
  "solo ícono"

### Requirement: Un objetivo por pantalla con lenguaje simple

Los componentes de layout base de pantalla provistos por esta slice SHALL estructurar el contenido alrededor
de un único objetivo por pantalla, sin exponer una API que permita combinar más de un objetivo principal en
la misma pantalla.

#### Scenario: Pantalla se construye con el layout base

- **WHEN** una pantalla del flujo de pago se construye usando el componente de layout base de pantalla
- **THEN** el layout expone un único punto de contenido principal (objetivo) y no permite declarar un
  segundo objetivo principal en la misma instancia

### Requirement: Elemento de ayuda visible en toda pantalla

Toda pantalla del flujo de pago construida sobre el layout base provisto por esta slice SHALL mostrar, sin
configuración adicional por pantalla, un elemento de ayuda visible equivalente a "¿Necesitas ayuda?".

#### Scenario: Pantalla usa el layout base sin configurar ayuda explícitamente

- **WHEN** una pantalla del flujo de pago se construye usando el layout base y no desactiva explícitamente
  el elemento de ayuda
- **THEN** el elemento de ayuda visible se muestra en la pantalla por defecto

### Requirement: Compatibilidad con lector de pantalla

Los componentes base del flujo de pago (texto, botón, ícono, layout de pantalla y estado "En proceso") SHALL
exponer roles y etiquetas (labels) accesibles que permitan a un lector de pantalla anunciar correctamente
cada elemento.

#### Scenario: Lector de pantalla navega una pantalla construida con los componentes base

- **WHEN** un lector de pantalla activo navega una pantalla del flujo de pago construida enteramente con los
  componentes base de esta slice
- **THEN** cada elemento interactivo o informativo relevante (botones, íconos, estados, elemento de ayuda) es
  anunciado con un rol y una etiqueta accesibles

### Requirement: Estado "En proceso" resiliente al cierre de la app

El componente base de estado "En proceso" provisto por esta slice SHALL mostrar un mensaje tranquilizador
(obtenido del catálogo de mensajes, ver capability `payment-ui-message-catalog`) y ese mensaje visual SHALL
mantenerse disponible si el pagador cierra y reabre la app mientras el estado sigue activo.

#### Scenario: Pagador cierra y reabre la app durante el estado "En proceso"

- **WHEN** una pantalla muestra el componente base de estado "En proceso" y el pagador cierra y vuelve a
  abrir la app mientras ese estado sigue vigente
- **THEN** la pantalla vuelve a mostrar el mensaje tranquilizador de "En proceso" para ese estado, sin que el
  componente de UI por sí solo pierda la indicación visual de que el intento sigue en curso

**Nota de alcance**: este requisito cubre el comportamiento de UI del componente de estado "En proceso"
(mensaje visual persistente); la persistencia real del intento de pago (reanudar la transacción subyacente
tras reabrir la app) depende de la integración definida en HU01-S1 y no es parte de esta capability.
