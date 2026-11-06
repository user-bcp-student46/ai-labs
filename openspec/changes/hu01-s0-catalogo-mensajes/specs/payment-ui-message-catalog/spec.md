# Spec Delta

## Purpose

Centraliza y hace editable todo el texto visible al pagador en las pantallas del flujo de pago, para que
ninguna pantalla hardcodee su propio copy y el contenido pueda cambiarse sin tocar la lógica de los
componentes.

## ADDED Requirements

### Requirement: Resolución de texto visible desde el catálogo

Cualquier texto visible al pagador en una pantalla del flujo de pago (saludo, resumen de confirmación,
estados terminales, ayuda, errores) SHALL obtenerse resolviendo una clave contra el catálogo de mensajes
centralizado, nunca escribiéndose literal dentro del componente de pantalla.

#### Scenario: Pantalla de flujo de pago solicita un texto por clave

- **WHEN** una pantalla del flujo de pago necesita mostrar un texto (por ejemplo, el saludo o un mensaje de
  error) e invoca el catálogo con la clave correspondiente
- **THEN** el catálogo devuelve el texto configurado para esa clave y la pantalla lo muestra sin contener el
  copy literal en su propio código

#### Scenario: Clave sin entrada configurada

- **WHEN** una pantalla solicita al catálogo una clave que no tiene entrada configurada
- **THEN** el catálogo devuelve un resultado identificable como "mensaje no configurado" (no vacío ni una
  excepción no controlada) para que la ausencia de copy sea detectable antes de llegar a producción

### Requirement: Catálogo editable sin tocar componentes

El contenido del catálogo de mensajes (los textos asociados a cada clave) SHALL poder modificarse sin
cambiar el código de los componentes de pantalla que los consumen.

#### Scenario: Se actualiza el texto de una clave existente

- **WHEN** se cambia el texto asociado a una clave del catálogo (por ejemplo, la etiqueta del estado
  "Exitoso")
- **THEN** toda pantalla que resuelva esa clave muestra el nuevo texto sin que su código fuente haya sido
  modificado

### Requirement: Cobertura de claves de las categorías del flujo

El catálogo SHALL exponer al menos una clave por cada categoría de texto identificada en el alcance de esta
slice: saludo, resumen de confirmación, estados terminales, ayuda y errores.

#### Scenario: Se listan las claves disponibles por categoría

- **WHEN** se consulta el catálogo por una de las categorías (saludo, resumen de confirmación, estados
  terminales, ayuda, errores)
- **THEN** el catálogo expone al menos una clave perteneciente a esa categoría

### Requirement: Mensaje tranquilizador de "En proceso" disponible en el catálogo

El catálogo SHALL incluir una clave para el mensaje tranquilizador del estado "En proceso", de modo que el
componente de UI base de ese estado (ver `payment-ui-accessible-components`) lo obtenga desde el catálogo en
lugar de definirlo en su propio código.

#### Scenario: El componente de estado "En proceso" resuelve su texto desde el catálogo

- **WHEN** el componente base que representa el estado "En proceso" necesita mostrar su mensaje
  tranquilizador
- **THEN** obtiene ese texto resolviendo la clave correspondiente del catálogo de mensajes
