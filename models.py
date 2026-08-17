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
