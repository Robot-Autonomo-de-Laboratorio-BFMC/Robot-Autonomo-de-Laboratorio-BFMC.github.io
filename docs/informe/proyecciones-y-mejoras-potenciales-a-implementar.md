# Proyecciones y Mejoras Potenciales a implementar

Este Trabajo Final de Grado ha logrado establecer una plataforma robótica funcional y un entorno de validación estandarizado. Sin embargo, dada la naturaleza iterativa de la ingeniería y la complejidad inherente a la conducción autónoma, se identifican áreas clave de mejora que constituyen una hoja de ruta (*roadmap*) para futuras líneas de investigación dentro del laboratorio. A continuación, se detallan las proyecciones técnicas sugeridas para elevar el nivel competitivo del prototipo:

### Evolución de la Arquitectura de Software (v2.0)

El análisis crítico del diseño actual (v1.0) revela oportunidades para migrar hacia una arquitectura más robusta, desacoplada y determinista.

- **Reingeniería de Alto Nivel (Brain):** Actualmente, existe una dependencia directa donde el controlador de señales gestiona al de navegación. Se propone la implementación de una **Arquitectura Basada en Eventos** o la introducción de un orquestador central que elimine esta dependencia circular. Asimismo, se sugiere formalizar las transiciones de estado (Pausa, Navegación, Maniobra) mediante una **Máquina de Estados Finita (FSM)** explícita, aumentando la seguridad del sistema ante conflictos lógicos.
- **Optimización de Bajo Nivel (Embedded):** Para reducir la latencia inherente al modelo de muestreo periódico (10ms), se proyecta una transición hacia un modelo **Event-Driven** (impulsado por eventos). Esto no solo eliminaría los tiempos de espera en la respuesta de los actuadores, sino que mejoraría la eficiencia energética, permitiendo que el procesador entre en estados de bajo consumo (*Idle*) durante los periodos de inactividad.

### Evolución del Sistema de Percepción (Sensor Fusion)

Si bien el enfoque *Vision-Only* ha demostrado ser efectivo para la navegación básica, la incorporación de redundancia sensorial es crítica para escenarios avanzados:

- **Visión Estereoscópica y Trasera:** Se recomienda la integración de una cámara posterior para eliminar los puntos ciegos, permitiendo maniobras de adelantamiento seguro y estacionamiento en reversa.
- **Robustez ante Condiciones Adversas:** Para garantizar la operación fuera del laboratorio, se sugiere someter al modelo YOLOv8 a pruebas de estrés (*stress testing*), simulando condiciones de baja visibilidad (niebla, humo) o saturación lumínica, y reentrenar la red neuronal con técnicas de *Data Augmentation* avanzadas.

### Algoritmos de Navegación y Control Avanzado

- Planificación de Rutas (Global Path Planning): Implementar algoritmos de teoría de grafos (como A\* o Dijkstra) sobre el mapa de la pista. Esto permitiría al vehículo calcular la ruta óptima entre dos puntos, tomando decisiones inteligentes en las intersecciones en lugar de reaccionar aleatoriamente o seguir un camino predefinido.
- Control de Crucero Adaptativo (ACC): Desarrollar un algoritmo de control longitudinal que ajuste la velocidad del motor en función de la curvatura de la pista o la distancia con un vehículo precedente, optimizando la estabilidad dinámica y emulando el comportamiento de un conductor humano experimentado.

### Conectividad V2X (Vehicle-to-Everything)

Siguiendo las tendencias de la industria y la competencia BFMC, el siguiente gran paso es la conectividad.

- Arquitectura Desacoplada: Se sugiere evaluar la incorporación de una Raspberry Pi como unidad secundaria dedicada exclusivamente a la comunicación. Mientras la NVIDIA Jetson se encarga del procesamiento pesado de IA, la Raspberry Pi gestionaría los protocolos MQTT para la comunicación V2X (vehículo a infraestructura) y V2V (vehículo a vehículo).
- Interacción con la Infraestructura: Implementar la comunicación bidireccional con los semáforos inteligentes desarrollados, permitiendo que el auto anticipe el estado del semáforo antes de tener contacto visual.

### Ampliación del Entorno de Validación

Para soportar estas nuevas funcionalidades, la infraestructura física debe crecer:

- Tráfico Dinámico: Introducir "coches obstáculo" móviles en la pista para simular situaciones de tráfico real, obligando al algoritmo a gestionar adelantamientos y distancias de seguridad.
- Geometrías Complejas: Ampliar la superficie de rodaje para incluir rotondas y carriles de incorporación, elementos que presentan desafíos lógicos superiores a las intersecciones simples en T o cruces de cuatro vías.
- Actualmente, se ha completado la primera etapa de fusión (Semáforos + Señales), pero sería positivo la incorporación de las clases de Autos y Peatones dentro de las variables a detectar mediante YOLO.
