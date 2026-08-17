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

# ---------------------------------------------------------------------------
# ReporteRecaudado
# ---------------------------------------------------------------------------

class ReporteRecaudado(BaseModel):
    cantidad_vendida: int = Field(..., description="cantidad de entradas vendidas")
    monto_total_facturado: float = Field(..., description="monto total facturado")
    fecha_generacion: datetime = Field(default_factory=datetime.now, description="fecha de generacion del reporte")

    def imprimir_reporte(self):
        reporte = (f"--- REPORTE RECAUDADO ({self.fecha_generacion.strftime('%d/%m/%Y %H:%M')}) ---\n"
                   f"Entradas vendidas: {self.cantidad_vendida}\n"
                   f"Monto total facturado: ${self.monto_total_facturado}")
        print(reporte)
        return reporte

    def guardar_pdf(self, nombre_archivo: str = "reporte.pdf"):
        print(f"Guardando el reporte en el archivo {nombre_archivo}...")
        return nombre_archivo

    def enviar_email(self, email: str):
        if "@" not in email:
            raise ValueError("El email no es valido")
        print(f"Enviando el reporte a {email}...")
        return True

# ---------------------------------------------------------------------------
# Espectaculo
# ---------------------------------------------------------------------------

class Espectaculo(BaseModel):
    nombre: str = Field(..., description="nombre del espectaculo")
    artista: str = Field(..., description="artista del espectaculo")
    lugar: str = Field(..., description="lugar donde se realiza")
    descripcion: Optional[str] = Field(default=None, description="descripcion del espectaculo")
    direccion_lugar: str = Field(..., description="direccion del lugar")

    funciones: List[Funcion] = Field(default_factory=list, description="funciones del espectaculo")
    reportes: List[ReporteRecaudado] = Field(default_factory=list, description="reportes generados")


    def agregar_funcion(self, funcion: Funcion):
        if funcion.fecha < datetime.now().date():
            raise ValueError("No se pueden registrar funciones pasadas")
        self.funciones.append(funcion)

    def consultar_disponibilidad(self):
        """Suma los lugares disponibles de todas las funciones."""
        disponibles = 0
        for funcion in self.funciones:
            disponibles += funcion.consultar_disponibilidad()
        return disponibles

    def contar_entradas_vendidas(self):
        cantidad = 0
        for funcion in self.funciones:
            cantidad += funcion.contar_entradas_vendidas()
        return cantidad

    def calcular_recaudacion(self):
        total = 0
        for funcion in self.funciones:
            total += funcion.calcular_recaudacion()
        return total

    def generar_reporte(self):
        """Crea un ReporteRecaudado con lo vendido hasta el momento."""
        reporte = ReporteRecaudado(
            cantidad_vendida=self.contar_entradas_vendidas(),
            monto_total_facturado=self.calcular_recaudacion()
        )
        self.reportes.append(reporte)
        return reporte

# ---------------------------------------------------------------------------
# Reserva
# ---------------------------------------------------------------------------

class Reserva(BaseModel):
    fecha_hora_reserva: datetime = Field(default_factory=datetime.now, description="fecha y hora de la reserva")
    monto_total: float = Field(default=0, description="monto total de la reserva")
    confirmada: bool = Field(default=False, description="indica si la reserva fue confirmada")

    entradas: List[Entrada] = Field(default_factory=list, description="entradas incluidas en la reserva")


    def agregar_entrada(self, entrada: Entrada):
        if self.confirmada:
            raise ValueError("No se pueden agregar entradas a una reserva ya confirmada")
        self.entradas.append(entrada)
        self.monto_total = self.calcular_monto_total()

    def calcular_monto_total(self):
        total = 0
        for entrada in self.entradas:
            total += entrada.importe_final
        return total

    def confirmar_reserva(self):
        if len(self.entradas) == 0:
            raise ValueError("ERROR! No se puede confirmar una reserva sin entradas")
        self.monto_total = self.calcular_monto_total()
        self.confirmada = True
        return self.monto_total

    def es_de_intervalo(self, fecha_desde: datetime, fecha_hasta: datetime):
        if fecha_desde <= self.fecha_hora_reserva <= fecha_hasta:
            return True
        else:
            return False

# ---------------------------------------------------------------------------
# Usuario
# ---------------------------------------------------------------------------

class Usuario(BaseModel):
    nombre: str = Field(..., min_length=3, description="nombre del usuario")
    email: str = Field(..., description="email del usuario")
    contraseña: str = Field(..., min_length=8, description="contraseña del usuario")

    reservas: List[Reserva] = Field(default_factory=list, description="reservas del usuario")

    @field_validator('email')
    @classmethod
    def validar_email(cls, valor: str):
        if "@" not in valor or "." not in valor:
            raise ValueError("El email no es valido")
        return valor

    def autenticar(self, contraseña: str):
        """Verifica la contraseña del usuario."""
        if self.contraseña == contraseña:
            return True
        else:
            return False

    def agregar_reserva(self, reserva: Reserva):
        self.reservas.append(reserva)

    def comprar_entradas(self, funcion_sector: FuncionSector, tipo_entrada: Tipo_Entrada, cantidad: int):
        """Emite 'cantidad' entradas de un sector y las agrupa en una reserva."""
        if not funcion_sector.hay_disponibilidad(cantidad):
            raise ValueError("No hay suficientes lugares disponibles")

        reserva = Reserva()
        for i in range(cantidad):
            entrada = funcion_sector.emitir_entrada(tipo_entrada)
            reserva.agregar_entrada(entrada)

        reserva.confirmar_reserva()
        self.agregar_reserva(reserva)
        return reserva

    def calcular_gasto_por_periodo(self, fecha_desde: datetime, fecha_hasta: datetime):
        total = 0
        for reserva in self.reservas:
            if reserva.es_de_intervalo(fecha_desde, fecha_hasta) and reserva.confirmada:
                total += reserva.monto_total
        return total


# ---------------------------------------------------------------------------
# Empresa
# ---------------------------------------------------------------------------

class Empresa(BaseModel):
    nombre: str = Field(..., description="nombre de la empresa")

    espectaculos: List[Espectaculo] = Field(default_factory=list, description="espectaculos de la empresa")
    usuarios: List[Usuario] = Field(default_factory=list, description="usuarios registrados")

    def agregar_espectaculo(self, espectaculo: Espectaculo):
        self.espectaculos.append(espectaculo)

    def agregar_usuario(self, usuario: Usuario):
        for registrado in self.usuarios:
            if registrado.email == usuario.email:
                raise ValueError("Ya existe un usuario con ese email")
        self.usuarios.append(usuario)

    def buscar_espectaculo(self, texto: str):
        """Busca espectaculos por nombre o por artista."""
        encontrados = []
        for espectaculo in self.espectaculos:
            if texto.lower() in espectaculo.nombre.lower() or texto.lower() in espectaculo.artista.lower():
                encontrados.append(espectaculo)
        return encontrados

    def generar_reportes(self):
        """Genera un reporte por cada espectaculo de la empresa."""
        reportes = []
        for espectaculo in self.espectaculos:
            reportes.append(espectaculo.generar_reporte())
        return reportes



# ---------------------------------------------------------------------------
# Programa principal de prueba (validacion)
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # --- Sectores ---
    SECTORES.append(Sector(nombre_sector="Campo", direccion="Av. Colon 1500",
                           ubicacion_de_cada_sector="Frente al escenario",
                           descripcion="Sector de pie", leyenda="Sin asiento",
                           capacidad_total=500))

    SECTORES.append(Sector(nombre_sector="Platea", direccion="Av. Colon 1500",
                           ubicacion_de_cada_sector="Lateral derecho",
                           descripcion="Sector con asientos numerados", leyenda="Numerado",
                           capacidad_total=200))

    # --- Tipos de entrada ---
    TIPOS_ENTRADA.append(Tipo_Entrada(descripcion="General", porcentaje_descuento=0))
    TIPOS_ENTRADA.append(Tipo_Entrada(descripcion="Estudiante", porcentaje_descuento=20))
    TIPOS_ENTRADA.append(Tipo_Entrada(descripcion="Jubilado", porcentaje_descuento=50))

    # --- FuncionSector (cruce Funcion x Sector) ---
    funcion_sector_campo = FuncionSector(sector=SECTORES[0],
                                         capacidad_disponible=500,
                                         precio_base=10000,
                                         horario_acceso=time(19, 0))

    funcion_sector_platea = FuncionSector(sector=SECTORES[1],
                                          capacidad_disponible=200,
                                          precio_base=18000,
                                          horario_acceso=time(19, 30))

    # --- Funcion ---
    hoy = datetime.now()

    funcion1 = Funcion(fecha=(hoy + timedelta(days=15)).date(),
                       hora_inicio=time(21, 0),
                       hora_fin=time(23, 30))

    funcion1.agregar_funcion_sector(funcion_sector_campo)
    funcion1.agregar_funcion_sector(funcion_sector_platea)

    # --- Espectaculo ---
    espectaculo1 = Espectaculo(nombre="Gira Nacional 2026",
                               artista="Los del Sur",
                               lugar="Estadio Kempes",
                               descripcion="Show de rock nacional",
                               direccion_lugar="Av. Cardenal Copello 700")

    espectaculo1.agregar_funcion(funcion1)
    ESPECTACULOS.append(espectaculo1)

    # --- Usuarios ---
    usuario1 = Usuario(nombre="Teo", email="teo@itsv.edu.ar", contraseña="123123123")
    USUARIOS.append(usuario1)

    # --- Empresa ---
    empresa = Empresa(nombre="TicketITSV")
    empresa.agregar_espectaculo(espectaculo1)
    empresa.agregar_usuario(usuario1)

    print("=== AUTENTICACION ===")
    print(f"Login correcto: {usuario1.autenticar('123123123')}")
    print(f"Login incorrecto: {usuario1.autenticar('otraclave')}")

    print("\n=== BUSQUEDA DE ESPECTACULOS ===")
    for espectaculo in empresa.buscar_espectaculo("gira"):
        print(f"{espectaculo.nombre} - {espectaculo.artista} - {espectaculo.lugar}")

    print("\n=== DISPONIBILIDAD INICIAL ===")
    print(f"Disponibilidad del espectaculo: {espectaculo1.consultar_disponibilidad()}")

    print("\n=== COMPRA DE ENTRADAS ===")
    reserva1 = usuario1.comprar_entradas(funcion_sector_campo, TIPOS_ENTRADA[0], 3)
    reserva2 = usuario1.comprar_entradas(funcion_sector_platea, TIPOS_ENTRADA[1], 2)

    for entrada in reserva1.entradas:
        entrada.imprimir_entrada()
    for entrada in reserva2.entradas:
        entrada.imprimir_entrada()

    reserva1.entradas[0].entregar_qr()

    print(f"\nMonto reserva 1: ${reserva1.monto_total} (confirmada: {reserva1.confirmada})")
    print(f"Monto reserva 2: ${reserva2.monto_total} (confirmada: {reserva2.confirmada})")

    print("\n=== DISPONIBILIDAD LUEGO DE LA VENTA ===")
    print(f"Campo: {funcion_sector_campo.consultar_disponibilidad()}")
    print(f"Platea: {funcion_sector_platea.consultar_disponibilidad()}")
    print(f"Total del espectaculo: {espectaculo1.consultar_disponibilidad()}")

    print("\n=== REPORTES ===")
    reportes = empresa.generar_reportes()
    for reporte in reportes:
        reporte.imprimir_reporte()
        reporte.guardar_pdf("reporte_gira_nacional.pdf")
        reporte.enviar_email(usuario1.email)

    print("\n=== GASTO DEL USUARIO EN EL PERIODO ===")
    fecha_desde = hoy - timedelta(days=30)
    fecha_hasta = hoy + timedelta(days=30)
    print(f"Gasto total: ${usuario1.calcular_gasto_por_periodo(fecha_desde, fecha_hasta)}")

    print("\n=== PRUEBAS DE VALIDACION ===")
    try:
        Funcion(fecha=hoy.date(), hora_inicio=time(22, 0), hora_fin=time(20, 0))
    except Exception as e:
        print("Error de validacion (horarios):", e)

    try:
        FuncionSector(sector=SECTORES[1], capacidad_disponible=999,
                      precio_base=1000, horario_acceso=time(19, 0))
    except Exception as e:
        print("Error de validacion (capacidad):", e)

    try:
        Usuario(nombre="Ana", email="anaitsv.edu.ar", contraseña="12345678")
    except Exception as e:
        print("Error de validacion (email):", e)

    try:
        Reserva().confirmar_reserva()
    except Exception as e:
        print("Error de validacion (reserva vacia):", e)
