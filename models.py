from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date, time, timedelta

# Listas "en memoria"
SECTORES = []
TIPOS_ENTRADA = []
ESPECTACULOS = []
USUARIOS = []

# Contador para numerar las entradas emitidas
ULTIMO_NUMERO_ENTRADA = 0

def proximo_numero_entrada():
    """Devuelve un número de entrada nuevo (autoincremental)."""
    global ULTIMO_NUMERO_ENTRADA
    ULTIMO_NUMERO_ENTRADA += 1
    return ULTIMO_NUMERO_ENTRADA

# ---------------------------------------------------------------------------
# Tipo_Entrada
# --------------------------------------------------------------------------

class Tipo_Entrada(BaseModel):
    descripcion: str = Field(..., description="descripcion del tipo de entrada (General, VIP, Jubilado...)")
    porcentaje_descuento: float = Field(default=0, description="porcentaje de descuento aplicado")
    precio_final: Optional[float] = Field(default=None, description="ultimo precio final calculado")

    @field_validator('porcentaje_descuento')
    @classmethod
    def validar_descuento(cls, valor: float):
        if valor < 0 or valor > 100:
            raise ValueError("El porcentaje de descuento debe estar entre 0 y 100")
        return valor

    def calcular_precio_final(self, precio_base: float):
        """Aplica el descuento sobre el precio base del sector."""
        if precio_base < 0:
            raise ValueError("El precio base no puede ser negativo")
        self.precio_final = precio_base - (precio_base * self.porcentaje_descuento / 100)
        return self.precio_final
        
# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------
    
class Entrada(BaseModel):
    numero_entrada: int = Field(..., description="numero de la entrada")
    fecha_hora_emision: datetime = Field(default_factory=datetime.now, description="fecha y hora de emision")
    importe_final: float = Field(..., description="importe final pagado por la entrada")
    codigo_qr: str = Field(..., description="codigo QR de la entrada")

    tipo_entrada: Tipo_Entrada = Field(..., description="tipo de entrada (1 sola)")

    
    @field_validator('importe_final')
    @classmethod
    def validar_importe(cls, valor: float):
        if valor < 0:
            raise ValueError("El importe final no puede ser negativo")
        return valor

    def imprimir_entrada(self):
        detalle = (f"ENTRADA N° {self.numero_entrada} | "
                   f"Tipo: {self.tipo_entrada.descripcion} | "
                   f"Importe: ${self.importe_final} | "
                   f"Emitida: {self.fecha_hora_emision.strftime('%d/%m/%Y %H:%M')}")
        print(detalle)
        return detalle

    def entregar_qr(self):
        print(f"Enviando codigo QR: {self.codigo_qr}")
        return self.codigo_qr

# ---------------------------------------------------------------------------
# Sector
# ---------------------------------------------------------------------------

class Sector(BaseModel):
    nombre_sector: str = Field(..., description="nombre del sector")
    direccion: str = Field(..., description="direccion del sector")
    ubicacion_de_cada_sector: str = Field(..., description="ubicacion del sector dentro del lugar")
    descripcion: Optional[str] = Field(default=None, description="descripcion del sector")
    leyenda: Optional[str] = Field(default=None, description="leyenda del sector")
    capacidad_total: int = Field(..., description="capacidad total del sector")

    @field_validator('capacidad_total')
    @classmethod
    def validar_capacidad(cls, valor: int):
        if valor <= 0:
            raise ValueError("La capacidad total debe ser mayor a 0")
        return valor

# ---------------------------------------------------------------------------
# FuncionSector (clase intermedia entre Funcion y Sector)
# ---------------------------------------------------------------------------

class FuncionSector(BaseModel):
    sector: Sector = Field(..., description="sector al que pertenece")
    capacidad_disponible: int = Field(..., description="lugares todavia disponibles")
    cantidad_entradas: int = Field(default=0, description="cantidad de entradas ya emitidas")
    precio_base: float = Field(..., description="precio base de la entrada en este sector")
    horario_acceso: time = Field(..., description="horario de acceso al sector")

    entradas: List[Entrada] = Field(default_factory=list, description="entradas emitidas para este sector")

    @field_validator('precio_base')
    @classmethod
    def validar_precio_base(cls, valor: float):
        if valor <= 0:
            raise ValueError("El precio base debe ser mayor a 0")
        return valor

    @model_validator(mode='after')
    def validar_capacidad_disponible(self):
        if self.capacidad_disponible < 0:
            raise ValueError("ERROR! La capacidad disponible no puede ser negativa")
        if self.capacidad_disponible > self.sector.capacidad_total:
            raise ValueError("ERROR! La capacidad disponible no puede superar la capacidad total del sector")
        return self

    def consultar_disponibilidad(self):
        return self.capacidad_disponible

    def hay_disponibilidad(self, cantidad: int = 1):
        if self.capacidad_disponible >= cantidad:
            return True
        else:
            return False

    def emitir_entrada(self, tipo_entrada: Tipo_Entrada):
        """Emite una entrada para este sector aplicando el tipo de entrada."""
        if not self.hay_disponibilidad(1):
            raise ValueError(f"No hay lugares disponibles en el sector {self.sector.nombre_sector}")

        importe = tipo_entrada.calcular_precio_final(self.precio_base)
        numero = proximo_numero_entrada()

        entrada = Entrada(
            numero_entrada=numero,
            importe_final=importe,
            codigo_qr=f"QR-{self.sector.nombre_sector}-{numero}",
            tipo_entrada=tipo_entrada
        )

        self.entradas.append(entrada)
        self.capacidad_disponible -= 1
        self.cantidad_entradas += 1
        return entrada

    def calcular_recaudacion(self):
        total = 0
        for entrada in self.entradas:
            total += entrada.importe_final
        return total

# ---------------------------------------------------------------------------
# Funcion
# ---------------------------------------------------------------------------

class Funcion(BaseModel):
    fecha: date = Field(..., description="fecha de la funcion")
    hora_inicio: time = Field(..., description="hora de inicio")
    hora_fin: time = Field(..., description="hora de fin")

    funciones_sector: List[FuncionSector] = Field(default_factory=list, description="sectores habilitados en la funcion")


    @model_validator(mode='after')
    def validar_coherencia_temporal(self):
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("ERROR! La hora de fin debe ser posterior a la hora de inicio")
        return self

    def agregar_funcion_sector(self, funcion_sector: FuncionSector):
        self.funciones_sector.append(funcion_sector)

    def consultar_disponibilidad(self):
        """Suma los lugares disponibles de todos los sectores de la funcion."""
        disponibles = 0
        for funcion_sector in self.funciones_sector:
            disponibles += funcion_sector.consultar_disponibilidad()
        return disponibles

    def buscar_sector(self, nombre_sector: str):
        for funcion_sector in self.funciones_sector:
            if funcion_sector.sector.nombre_sector == nombre_sector:
                return funcion_sector
        raise ValueError(f"No existe el sector {nombre_sector} en esta funcion")

    def es_de_intervalo(self, fecha_desde: date, fecha_hasta: date):
        if fecha_desde <= self.fecha <= fecha_hasta:
            return True
        else:
            return False

    def contar_entradas_vendidas(self):
        cantidad = 0
        for funcion_sector in self.funciones_sector:
            cantidad += funcion_sector.cantidad_entradas
        return cantidad

    def calcular_recaudacion(self):
        total = 0
        for funcion_sector in self.funciones_sector:
            total += funcion_sector.calcular_recaudacion()
        return total



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
