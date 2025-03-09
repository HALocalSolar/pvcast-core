# pvcast

The software architecture of the entire project looks something like this (preliminary):

```mermaid
flowchart LR

    subgraph pvcast-addon
        direction TB
        B[pvcast-core]
        F[pvcast-frontend]

        F .->|pvconfig.yaml| B
    end

    subgraph homeassistant
        C[pvcast-python]
        E[weater integration]

        direction RL
    end

pvcast-addon <-->|REST API| homeassistant
```

While the class diagram of `pvcast-core` looks like this:

```mermaid
classDiagram
    class ConfigReader{
        +dict config 
        -Schema schema 
    }


    class OpenMeteo{
    }

    class HAEntity{
    }

    class Webserver{
    }

    class WeatherSource{
    }

    class PVPlantModel{
    }

    WeatherSource <|-- HAEntity 
    WeatherSource <|-- OpenMeteo 
    Webserver <-- PVPlantModel 
    PVPlantModel <-- ConfigReader 
    Webserver <-- WeatherSource 
```
