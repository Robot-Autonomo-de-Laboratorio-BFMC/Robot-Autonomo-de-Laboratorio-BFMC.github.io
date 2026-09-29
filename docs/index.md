<div class="hero" markdown>

# Robot Autónomo de Laboratorio { .hero__title }

<div class="hero__meta">
  <span class="hero__tag">Bosch Future Mobility Challenge</span>
  <span class="hero__tag">Escala 1:10</span>
  <span class="hero__tag">Universidad Austral</span>
</div>

<div class="hero__body" markdown>
<div class="hero__text" markdown>

<p class="hero__lead">
Vehículo autónomo a escala capaz de mantenerse en carril, reconocer señales de
tránsito y semáforos, y reaccionar ante obstáculos, sobre una maqueta construida
en el laboratorio.
</p>

<p class="hero__lead">
Este sitio reúne la documentación técnica del proyecto, el informe de tesis
completo, los resultados de entrenamiento y la bitácora de cómo se fue
construyendo.
</p>

<p class="hero__links">
  <a href="timeline/">Cómo llegamos acá</a>
  <a href="arquitectura/">Arquitectura</a>
</p>

</div>
<figure class="hero__figure" markdown>
![El equipo presentando el proyecto ante el jurado, con la pista en primer plano](assets/defensa-pista.jpg){ .hero__crop }
<figcaption class="hero__caption">
La defensa del trabajo de grado: el equipo frente al jurado, con la pista y los
vehículos en primer plano.
</figcaption>
</figure>
</div>
</div>

---

## Por dónde empezar

<div class="grid cards" markdown>

-   **:material-timeline-clock: [Cómo llegamos acá](timeline.md)**

    La bitácora del proyecto: de un trabajo práctico de la materia Visión
    Artificial a un auto que maneja solo.

-   **:material-sitemap: [Arquitectura](arquitectura/index.md)**

    Los dos subsistemas —VCU sobre ESP32 y Brain sobre Jetson— y el protocolo UART
    que los une.

-   **:material-eye: [Visión artificial](vision/index.md)**

    El detector YOLOv8, los datasets, y los informes de entrenamiento con métricas.

-   **:material-notebook: [Bitácora de laboratorio](archivo/notion/jetson/index.md)**

    Puesta a punto de la Jetson y del detector de líneas, paso a paso.

</div>

## El sistema en una imagen

```mermaid
flowchart LR
    subgraph JETSON["Jetson Orin Nano — brain"]
        CAM[Cámara] --> LANE[Detección de carril]
        CAM --> SIGN[Detección de señales<br/>YOLOv8 + TensorRT]
        LANE --> PID[Control PID lateral]
        SIGN --> STRAT[Estrategias<br/>intersección · semáforo]
        STRAT -.interrumpe.-> PID
        PID --> DASH[Dashboard web]
    end
    subgraph ESP["ESP32 — embedded"]
        UART[Parser UART] --> MOT[Motor 100Hz]
        UART --> STEER[Servo dirección 100Hz]
        US[HC-SR04] --> EMG[Parada de emergencia]
        EMG -.prioridad.-> MOT
    end
    PID -->|UART| UART
    STRAT -->|UART| UART
    UART -->|eventos| DASH
```

La frontera entre los dos bloques es física —dos computadoras distintas— y está
definida por el enlace UART. El ESP32 nunca confía
en la Jetson: valida la frescura de cada dato con un **TTL** y frena solo si el
enlace se cae.

<figure class="band" markdown>
![Raúl, el vehículo, sobre la pista del laboratorio](assets/raul-en-pista.jpg){ .band__portrait }
<figcaption>
Raúl: cámara Intel RealSense sobre el mástil, Jetson Orin Nano, sensor
ultrasónico en soporte impreso y chasis Tamiya 1:10 en MDF cortado.
</figcaption>
</figure>

## Los repositorios

| Repo | Qué contiene | Plataforma | Licencia |
|---|---|---|---|
| [`brain`](https://github.com/Robot-Autonomo-de-Laboratorio-BFMC/brain) | Percepción, navegación, estrategias de maniobra y dashboard | Jetson Orin Nano / Python | — |
| [`embedded`](https://github.com/Robot-Autonomo-de-Laboratorio-BFMC/embedded) | Firmware de control de bajo nivel, seguridad, UART | ESP32 / FreeRTOS | **MIT** |
| [`vision-artificial`](https://github.com/Robot-Autonomo-de-Laboratorio-BFMC/vision-artificial) | Entrenamiento YOLOv8, datasets, informes, inferencia | Colab / Docker | — |
| [`*.github.io`](https://github.com/Robot-Autonomo-de-Laboratorio-BFMC/Robot-Autonomo-de-Laboratorio-BFMC.github.io) | Este sitio | MkDocs | — |

!!! info "Sobre el reuso"
    El firmware de la VCU (`embedded`) está publicado bajo **licencia MIT**: se
    puede usar, modificar y redistribuir citando a los autores. Es la pieza pensada
    para que el próximo equipo arranque desde algo que ya funciona, en vez de
    desde cero.

    Los demás repositorios todavía no declaran licencia, lo que por defecto
    significa *todos los derechos reservados*.
