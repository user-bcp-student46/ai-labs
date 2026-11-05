## ADDED Requirements

### Requirement: Las credenciales se tratan como datos en el login
El sistema SHALL evaluar `username` y `password` de `POST /auth/login` únicamente como valores de entrada y no como parte de la sentencia SQL de consulta de usuarios, de modo que ningún valor enviado por el cliente pueda alterar la lógica de la consulta.

#### Scenario: Inyección SQL en el usuario
- **WHEN** se envía `POST /auth/login` con `username` igual a `' OR '1'='1` y una contraseña cualquiera
- **THEN** la respuesta es `401`
- **AND** el cuerpo no contiene `token`

#### Scenario: Inyección SQL en la contraseña
- **WHEN** se envía `POST /auth/login` con `username` igual a `student` y `password` igual a `' OR '1'='1`
- **THEN** la respuesta es `401`
- **AND** el cuerpo no contiene `token`

#### Scenario: Comentario SQL en el usuario
- **WHEN** se envía `POST /auth/login` con `username` igual a `student'--` y una contraseña cualquiera
- **THEN** la respuesta es `401`
- **AND** el cuerpo no contiene `token`

#### Scenario: Valor con comilla simple sin intención de inyección
- **WHEN** se envía `POST /auth/login` con `username` igual a `o'brien` y una contraseña cualquiera
- **THEN** la respuesta es `401` y no `500`

### Requirement: El login con credenciales válidas conserva su contrato
El sistema SHALL responder `200` a `POST /auth/login` con credenciales válidas, incluyendo `token`, `expiresIn`, `user.username`, `user.displayName`, `user.role` y `debug`, sin cambios respecto al comportamiento previo.

#### Scenario: Login del usuario student
- **WHEN** se envía `POST /auth/login` con `username` igual a `student` y `password` igual a `Workshop123!`
- **THEN** la respuesta es `200`
- **AND** `user.username` es `student`, `user.role` es `STUDENT` y `token` no es nulo
- **AND** `expiresIn` es `3600`

#### Scenario: Login del usuario trainer
- **WHEN** se envía `POST /auth/login` con `username` igual a `trainer` y `password` igual a `Trainer123!`
- **THEN** la respuesta es `200`
- **AND** `user.username` es `trainer` y `token` no es nulo

### Requirement: Las credenciales incorrectas y las entradas incompletas conservan sus respuestas
El sistema SHALL responder `401` con un `message` y sin `token` cuando las credenciales no corresponden a ningún usuario, y `400` con un `message` cuando falta `username` o `password` (o están en blanco) o el cuerpo es nulo.

#### Scenario: Contraseña incorrecta
- **WHEN** se envía `POST /auth/login` con `username` igual a `student` y una contraseña incorrecta
- **THEN** la respuesta es `401`
- **AND** el cuerpo incluye `message` y no incluye `token`

#### Scenario: Usuario inexistente
- **WHEN** se envía `POST /auth/login` con un `username` que no existe
- **THEN** la respuesta es `401` y no incluye `token`

#### Scenario: Usuario ausente o en blanco
- **WHEN** se envía `POST /auth/login` sin `username` o con `username` en blanco
- **THEN** la respuesta es `400` con `message` igual a `Username is required`

#### Scenario: Contraseña ausente o en blanco
- **WHEN** se envía `POST /auth/login` con `username` válido y sin `password` o con `password` en blanco
- **THEN** la respuesta es `400` con `message` igual a `Password is required`

### Requirement: El intento de inyección está cubierto por pruebas automatizadas
El componente `auth/` SHALL incluir en `AuthResourceTest` al menos una prueba que ejecute un intento de inyección SQL contra `POST /auth/login` y verifique `401` sin `token`, y la suite SHALL pasar al ejecutar `mvn test` desde `auth/`.

#### Scenario: Prueba de inyección presente y verde
- **WHEN** se ejecuta `mvn test` desde `auth/`
- **THEN** `AuthResourceTest` ejecuta el caso de inyección con `' OR '1'='1`
- **AND** la suite completa termina sin fallos
