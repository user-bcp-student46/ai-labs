# Tasks

Alcance: `web/` únicamente (ver `proposal.md`). Ejecutar pruebas con `python tools/lab.py test web` desde la
raíz, o `npm test` / `npm run test:coverage` desde `web/`. No se modifican `LoginComponent`,
`DashboardComponent` ni los contratos `/auth/login` y `/api/tasks`.

## 1. Estructura del módulo compartido

- [x] 1.1 Crear el directorio `web/src/app/payment-ui/` con subcarpetas `messages/` y `components/` (ver
  `design.md` - Decisions), sin modificar `login/` ni `dashboard/`. Verificar ejecutando
  `npm test` desde `web/` y confirmando que la suite existente sigue en verde (sin romper nada por la
  nueva carpeta vacía).
  **Evidencia**: directorios creados; `LoginComponent`/`DashboardComponent` sin cambios (confirmado con
  `git status`). `npm test` (web) en verde tras agregar el primer archivo del módulo (ver evidencia de 2.1).

## 2. Catálogo de mensajes (`payment-ui-message-catalog`)

- [x] 2.1 Implementar el servicio de catálogo (p. ej. `MessageCatalogService`) en `payment-ui/messages/` con
  un método de resolución por clave y una fuente de configuración editable (claves por categoría: saludo,
  resumen de confirmación, estados terminales, ayuda, errores), incluyendo la clave del mensaje
  tranquilizador de "En proceso". Verificar con una prueba unitaria que resuelve al menos una clave real por
  categoría y obtiene el texto configurado.
  **Evidencia**: `message-catalog.ts` (9 claves en 5 categorías) + `message-catalog.service.ts`;
  `message-catalog.spec.ts` (6 tests). `npm test` (web) → 2 archivos, 7 tests passed (16:09:40).
- [x] 2.2 Implementar el comportamiento ante clave no configurada (retorno identificable como "mensaje no
  configurado", sin excepción no controlada). Verificar con una prueba unitaria que solicita una clave
  inexistente y comprueba el resultado identificable.
  **Evidencia**: `resolveMessage` devuelve `[mensaje no configurado: <clave>]`; cubierto por
  `message-catalog.spec.ts` ("devuelve un resultado identificable..."), incluido en la corrida anterior.
- [x] 2.3 Verificar que editar el texto de una clave existente en la fuente de configuración no requiere
  cambios en ningún componente consumidor. Verificar con una prueba unitaria que cambia el valor de una
  clave en la configuración de prueba y confirma que el servicio devuelve el nuevo valor sin tocar otros
  archivos.
  **Evidencia**: prueba "refleja un texto editado sin cambiar la función de resolución ni el servicio" en
  `message-catalog.spec.ts`, incluida en la corrida anterior.

## 3. Componentes de UI base accesibles (`payment-ui-accessible-components`)

- [x] 3.1 Implementar el componente de texto base en `payment-ui/components/` que aplique tamaño ≥ 18 px y
  contraste WCAG AA vía CSS propio. Verificar con una prueba de componente que inspecciona el tamaño de
  fuente y el contraste calculado (o las variables/clases CSS que lo garantizan) del elemento renderizado.
  **Evidencia**: `payment-text.component.ts/css`; sin DOM/TestBed disponible (`vitest.config.ts` usa
  `environment: 'node'`), la prueba verifica las constantes exportadas y el contenido real del CSS
  (`payment-text.component.spec.ts`, 3 tests). `npm test` (web) en verde (ver evidencia 4.1).
- [x] 3.2 Implementar el componente de botón base con área táctil ≥ 48 px y rol/label accesibles. Verificar
  con una prueba de componente que mide las dimensiones renderizadas y confirma el atributo de accesibilidad
  (`role`/`aria-label`) presente.
  **Evidencia**: `payment-button.component.ts/css`; `payment-button.component.spec.ts` (3 tests) verifica
  el CSS (`min-width`/`min-height: 48px`) y el binding `[attr.aria-label]` en el `<button>` nativo.
- [x] 3.3 Implementar el componente de ícono+texto base sin modo "solo ícono" (API que siempre exige un
  texto asociado). Verificar con una prueba de componente que confirma que el texto es obligatorio
  (falla o se omite el render si no se provee) y que el ícono se marca `aria-hidden` mientras el texto es
  anunciado.
  **Evidencia**: `payment-icon-text.component.ts`; `payment-icon-text.component.spec.ts` (4 tests) cubre
  `canRender` (false sin texto/solo espacios, true con texto) y el `aria-hidden="true"` del ícono.
- [x] 3.4 Implementar el componente de layout base de pantalla con un único punto de contenido principal y
  el elemento de ayuda visible ("¿Necesitas ayuda?") mostrado por defecto. Verificar con una prueba de
  componente que renderiza el layout sin configuración adicional y confirma la presencia del elemento de
  ayuda.
  **Evidencia**: `payment-screen-layout.component.ts`; `payment-screen-layout.component.spec.ts` (4 tests)
  confirma un único `<ng-content>`, `showHelp` por defecto `true` y el texto resuelto desde el catálogo.
- [x] 3.5 Implementar el componente base de estado "En proceso", que resuelve su mensaje desde el catálogo
  de mensajes (tarea 2.1) y persiste su bandera de "en curso" en almacenamiento local del navegador (ver
  `design.md` - Decisions). Verificar con una prueba de componente que simula recarga (reinstanciar el
  componente con el mismo almacenamiento local) y confirma que el mensaje tranquilizador se vuelve a
  mostrar.
  **Evidencia**: `processing-state-storage.ts` (funciones puras) + `payment-processing-state.component.ts`;
  `processing-state-storage.spec.ts` (3 tests) y `payment-processing-state.component.spec.ts` (5 tests,
  incluye instanciar un segundo componente sobre el mismo `localStorage` simulado para simular recarga).
- [x] 3.6 Verificar compatibilidad con lector de pantalla de los cinco componentes base (texto, botón,
  ícono+texto, layout, estado "En proceso"): cada uno expone roles/labels accesibles. Verificar con pruebas
  de componente que consultan los atributos ARIA renderizados de cada uno.
  **Evidencia**: `components/accessibility.spec.ts` (5 tests), uno por componente, más las aserciones ARIA
  ya incluidas en cada spec dedicado.

## 4. Verificación y evidencia

- [x] 4.1 Ejecutar `npm run test:coverage` desde `web/` (o `python tools/lab.py test web` desde la raíz) y
  confirmar que toda la suite (existente + nueva) pasa en verde.
  **Evidencia**: `python tools/lab.py test web` → `npm test` 39 passed (39) en 10 archivos; `npm run
  test:coverage` 39 passed (39); `npm run build` exitoso (ver `web-hu01-s0-test-output.txt` y la sección
  `web` de `HALLAZGOS.md`). Verificación adicional: `npx tsc --noEmit -p tsconfig.json` sin errores.
- [x] 4.2 Confirmar que la cobertura del código modificado/agregado en `payment-ui/` alcanza ≥ 85% según el
  reporte de `test:coverage`.
  **Evidencia**: reporte v8 de `npm run test:coverage` → 100% de sentencias/ramas/funciones/líneas en
  todos los archivos bajo `src/app/payment-ui/` (catálogo, `color-contrast.ts` y los cinco componentes).
- [x] 4.3 Registrar en el documento general de hallazgos la sección `web`, con el resultado de las pruebas y
  la cobertura obtenida para esta slice (HU01-S0), sin tocar otras secciones del documento.
  **Evidencia**: sección `## web` → `### HU01-S0 — Catálogo de mensajes...` agregada al final de
  `HALLAZGOS.md`; secciones `auth`, `api`, `Contrato observado`, `Matriz de seguimiento` y `Discovery
  adicional — api` sin modificar.

## Fuera de alcance (no incluir en estas tareas)

- Construcción de las pantallas funcionales del flujo de pago (saludo, confirmación, resultados,
  orquestador): corresponde a HU01-S1–S4.
- Copy final de los mensajes (etiquetas de estados terminales, textos de ayuda definitivos): pendiente con
  producto.
- Persistencia real del intento de pago en backend: corresponde a la integración de HU01-S1.
- Cambios en `auth/` o `api/`, en `LoginComponent`, `DashboardComponent`, o en los contratos `/auth/login` y
  `/api/tasks`.
