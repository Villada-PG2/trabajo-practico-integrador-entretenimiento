# Sistema de Venta de Entradas para Espectáculos

Proyecto en **Python + Pydantic** que implementa el modelo de clases de un sistema de venta de entradas para espectáculos (recitales, obras de teatro, etc.).

Cada clase del diagrama de clases es un modelo (`BaseModel`), cada atributo es un campo tipado y cada relación `1..*` es una lista de modelos anidados.

## Requisitos

- Python 3.10 o superior
- Pydantic v2

```bash
pip install pydantic
```

## Ejecución

```bash
python Resolucion_Espectaculos.py
```

El archivo incluye un bloque de prueba (`if __name__ == "__main__":`) que crea los datos, vende entradas, genera reportes y muestra los errores de validación.

---

## Estructura del proyecto

Son 10 clases agrupadas en cuatro roles:

| Rol | Clases | Para qué sirve |
|---|---|---|
| **Catálogo** | `Empresa`, `Espectaculo`, `Funcion` | La empresa organiza espectáculos y cada espectáculo tiene varias funciones (fechas) |
| **Capacidad y precio** | `Sector`, `FuncionSector` | `Sector` es el lugar físico (Campo, Platea). `FuncionSector` cruza función + sector y guarda el precio y la disponibilidad de esa combinación |
| **Venta** | `Usuario`, `Reserva`, `Entrada`, `Tipo_Entrada` | El usuario compra, la reserva agrupa entradas y el tipo de entrada define el descuento |
| **Reportes** | `ReporteRecaudado` | Resumen de lo vendido por espectáculo |

### Diagrama

```mermaid
classDiagram
    class Empresa {
        +string nombre
        +buscar_espectaculo()
        +generar_reportes()
    }
    class Usuario {
        +string nombre
        +string email
        +string contraseña
        +autenticar()
        +comprar_entradas()
    }
    class Espectaculo {
        +string nombre
        +string artista
        +string lugar
        +string direccion_lugar
        +consultar_disponibilidad()
        +generar_reporte()
    }
    class Funcion {
        +date fecha
        +time hora_inicio
        +time hora_fin
        +consultar_disponibilidad()
    }
    class Sector {
        +string nombre_sector
        +string ubicacion_de_cada_sector
        +int capacidad_total
    }
    class FuncionSector {
        +int capacidad_disponible
        +int cantidad_entradas
        +float precio_base
        +time horario_acceso
        +emitir_entrada()
    }
    class Reserva {
        +DateTime fecha_hora_reserva
        +float monto_total
        +confirmar_reserva()
    }
    class Entrada {
        +int numero_entrada
        +DateTime fecha_hora_emision
        +float importe_final
        +string codigo_qr
        +imprimir_entrada()
        +entregar_qr()
    }
    class Tipo_Entrada {
        +string descripcion
        +float porcentaje_descuento
        +calcular_precio_final()
    }
    class ReporteRecaudado {
        +int cantidad_vendida
        +float monto_total_facturado
        +imprimir_reporte()
    }

    Empresa --> "1..*" Espectaculo
    Empresa --> "1..*" Usuario
    Espectaculo --> "1..*" Funcion
    Funcion --> "1..*" FuncionSector
    Sector --> "1..*" FuncionSector
    Usuario --> "1..*" Reserva
    Reserva --> "1..*" Entrada
    FuncionSector --> "1..*" Entrada
    Entrada --> "1" Tipo_Entrada
    Espectaculo --> "1..*" ReporteRecaudado
```

---

## Flujo principal

Todo el proceso de venta se dispara con un solo método:

```python
reserva = usuario.comprar_entradas(funcion_sector, tipo_entrada, cantidad)
```

Que por dentro hace:

1. Verifica que haya lugares disponibles en el `FuncionSector`.
2. Crea una `Reserva` vacía.
3. Por cada entrada pedida, el `FuncionSector` la emite: `Tipo_Entrada` aplica el descuento sobre el `precio_base`, se generan el número y el código QR, se descuenta un lugar y se suma uno al contador de entradas.
4. Cada `Entrada` se agrega a la reserva y se recalcula el monto total.
5. Se confirma la reserva y se asocia al usuario.

La misma instancia de `Entrada` queda referenciada por el `FuncionSector` y por la `Reserva`, cumpliendo las dos relaciones del diagrama sin generar referencias circulares (que Pydantic no puede validar).

---

## Cálculo de totales

Los totales se calculan en cascada, hacia abajo, así nunca queda un valor desactualizado:

```
Espectaculo.calcular_recaudacion()
    └── suma Funcion.calcular_recaudacion()
            └── suma FuncionSector.calcular_recaudacion()
                    └── suma entrada.importe_final
```

`generar_reporte()` usa esos totales para crear el `ReporteRecaudado` con la cantidad vendida y el monto facturado.

---

## Validaciones

El proyecto usa tres niveles de validación:

**1. Tipos** — automático de Pydantic: verifica y convierte `int`, `float`, `str`, `date`, `time` y `datetime`.

**2. `@field_validator`** — valida un campo por separado:

| Modelo | Campo | Regla |
|---|---|---|
| `Tipo_Entrada` | `porcentaje_descuento` | Entre 0 y 100 |
| `Entrada` | `importe_final` | No puede ser negativo |
| `Sector` | `capacidad_total` | Mayor a 0 |
| `FuncionSector` | `precio_base` | Mayor a 0 |
| `Usuario` | `email` | Debe contener `@` y `.` |

**3. `@model_validator(mode='after')`** — valida varios campos juntos:

| Modelo | Regla |
|---|---|
| `Funcion` | `hora_fin` debe ser posterior a `hora_inicio` |
| `FuncionSector` | `capacidad_disponible` no puede ser negativa ni superar la `capacidad_total` del sector |

**Reglas de negocio** — van con `raise ValueError` dentro de los métodos, no en validadores, porque dependen del momento en que se ejecuta la acción y no de la creación del objeto:

- No se pueden emitir entradas sin lugares disponibles.
- No se puede confirmar una reserva vacía.
- No se pueden agregar entradas a una reserva ya confirmada.
- No se pueden registrar funciones con fecha pasada.
- No se puede registrar dos usuarios con el mismo email.

---

## Ejemplo de uso

```python
from datetime import datetime, time, timedelta

# Sector y tipo de entrada
campo = Sector(nombre_sector="Campo", direccion="Av. Colon 1500",
               ubicacion_de_cada_sector="Frente al escenario", capacidad_total=500)
estudiante = Tipo_Entrada(descripcion="Estudiante", porcentaje_descuento=20)

# Precio y disponibilidad para esa función
fs_campo = FuncionSector(sector=campo, capacidad_disponible=500,
                         precio_base=10000, horario_acceso=time(19, 0))

# Función y espectáculo
funcion = Funcion(fecha=(datetime.now() + timedelta(days=15)).date(),
                  hora_inicio=time(21, 0), hora_fin=time(23, 30))
funcion.agregar_funcion_sector(fs_campo)

show = Espectaculo(nombre="Gira Nacional 2026", artista="Los del Sur",
                   lugar="Estadio Kempes", direccion_lugar="Av. Cardenal Copello 700")
show.agregar_funcion(funcion)

# Empresa y usuario
empresa = Empresa(nombre="TicketITSV")
usuario = Usuario(nombre="Teo", email="teo@itsv.edu.ar", contraseña="123123123")
empresa.agregar_espectaculo(show)
empresa.agregar_usuario(usuario)

# Compra y reporte
usuario.autenticar("123123123")
reserva = usuario.comprar_entradas(fs_campo, estudiante, 2)
show.generar_reporte().imprimir_reporte()
```

---

## Decisiones de diseño

- **`FuncionSector` como clase intermedia:** el precio y la disponibilidad no pertenecen al sector físico sino a la combinación función + sector, porque el mismo Campo puede costar distinto en dos fechas.
- **Sin referencias circulares:** `Entrada` no guarda referencias hacia arriba; la relación doble se resuelve compartiendo la misma instancia entre las dos listas.
- **Los cálculos son métodos, no validadores:** un `@model_validator` se ejecuta al crear el objeto y debe devolver `self`, por lo que no sirve para devolver totales.
- **`default_factory=list`:** evita el error de la lista mutable compartida entre instancias.

## Posibles mejoras

- Persistir los datos en JSON con `model_dump_json()` y `model_validate_json()`.
- Generar el código QR real con la librería `qrcode` y exportar el reporte con `reportlab`.
- Hashear la contraseña en lugar de guardarla en texto plano.
- Validar el email con `EmailStr` de `pydantic[email]`.
