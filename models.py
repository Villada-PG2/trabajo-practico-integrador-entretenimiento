from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date, time, timedelta

class Tipo_Entrada(BaseModel):
    descripcion: str = Field(..., description="descripcion del tipo de entrada (General, VIP, Jubilado...)")
    porcentaje_descuento: float = Field(default=0, description="porcentaje de descuento aplicado")
    precio_final: Optional[float] = Field(default=None, description="ultimo precio final calculado")

class Entrada(BaseModel):
    numero_entrada: int = Field(..., description="numero de la entrada")
    fecha_hora_emision: datetime = Field(default_factory=datetime.now, description="fecha y hora de emision")
    importe_final: float = Field(..., description="importe final pagado por la entrada")
    codigo_qr: str = Field(..., description="codigo QR de la entrada")

    tipo_entrada: Tipo_Entrada = Field(..., description="tipo de entrada (1 sola)")

class Sector(BaseModel):
    nombre_sector: str = Field(..., description="nombre del sector")
    direccion: str = Field(..., description="direccion del sector")
    ubicacion_de_cada_sector: str = Field(..., description="ubicacion del sector dentro del lugar")
    descripcion: Optional[str] = Field(default=None, description="descripcion del sector")
    leyenda: Optional[str] = Field(default=None, description="leyenda del sector")
    capacidad_total: int = Field(..., description="capacidad total del sector")

class FuncionSector(BaseModel):
    sector: Sector = Field(..., description="sector al que pertenece")
    capacidad_disponible: int = Field(..., description="lugares todavia disponibles")
    cantidad_entradas: int = Field(default=0, description="cantidad de entradas ya emitidas")
    precio_base: float = Field(..., description="precio base de la entrada en este sector")
    horario_acceso: time = Field(..., description="horario de acceso al sector")

    entradas: List[Entrada] = Field(default_factory=list, description="entradas emitidas para este sector")

class Funcion(BaseModel):
    fecha: date = Field(..., description="fecha de la funcion")
    hora_inicio: time = Field(..., description="hora de inicio")
    hora_fin: time = Field(..., description="hora de fin")

    funciones_sector: List[FuncionSector] = Field(default_factory=list, description="sectores habilitados en la funcion")


class ReporteRecaudado(BaseModel):
    cantidad_vendida: int = Field(..., description="cantidad de entradas vendidas")
    monto_total_facturado: float = Field(..., description="monto total facturado")
    fecha_generacion: datetime = Field(default_factory=datetime.now, description="fecha de generacion del reporte")

class Espectaculo(BaseModel):
    nombre: str = Field(..., description="nombre del espectaculo")
    artista: str = Field(..., description="artista del espectaculo")
    lugar: str = Field(..., description="lugar donde se realiza")
    descripcion: Optional[str] = Field(default=None, description="descripcion del espectaculo")
    direccion_lugar: str = Field(..., description="direccion del lugar")

    funciones: List[Funcion] = Field(default_factory=list, description="funciones del espectaculo")
    reportes: List[ReporteRecaudado] = Field(default_factory=list, description="reportes generados")

class Reserva(BaseModel):
    fecha_hora_reserva: datetime = Field(default_factory=datetime.now, description="fecha y hora de la reserva")
    monto_total: float = Field(default=0, description="monto total de la reserva")
    confirmada: bool = Field(default=False, description="indica si la reserva fue confirmada")

    entradas: List[Entrada] = Field(default_factory=list, description="entradas incluidas en la reserva")

class Usuario(BaseModel):
    nombre: str = Field(..., min_length=3, description="nombre del usuario")
    email: str = Field(..., description="email del usuario")
    contraseña: str = Field(..., min_length=8, description="contraseña del usuario")

    reservas: List[Reserva] = Field(default_factory=list, description="reservas del usuario")

class Empresa(BaseModel):
    nombre: str = Field(..., description="nombre de la empresa")

    espectaculos: List[Espectaculo] = Field(default_factory=list, description="espectaculos de la empresa")
    usuarios: List[Usuario] = Field(default_factory=list, description="usuarios registrados")