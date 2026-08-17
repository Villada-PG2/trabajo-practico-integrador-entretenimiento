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