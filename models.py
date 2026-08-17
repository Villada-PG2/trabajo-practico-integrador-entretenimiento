from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date, time, timedelta

class Tipo_Entrada(BaseModel):
    descripcion: str = Field(..., description="descripcion del tipo de entrada (General, VIP, Jubilado...)")
    porcentaje_descuento: float = Field(default=0, description="porcentaje de descuento aplicado")
    precio_final: Optional[float] = Field(default=None, description="ultimo precio final calculado")