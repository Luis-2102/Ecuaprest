# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    cedula = db.Column(db.String, nullable=False)
    contrato = db.Column(db.String, nullable=False)
    numero_cuenta = db.Column(db.String, nullable=False)
    correo = db.Column(db.String, unique=True, nullable=False)
    telefono = db.Column(db.String)

    documentos = db.relationship('Documento', backref='cliente', lazy=True)
    deudas = db.relationship('Deuda', backref='cliente', lazy=True)
    pagos = db.relationship('Pago', backref='cliente', lazy=True)


class Documento(db.Model):
    __tablename__ = 'documentos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    archivo = db.Column(db.LargeBinary, nullable=False)
    nombre_archivo = db.Column(db.String, nullable=False)
    tipo_archivo = db.Column(db.String, default='pdf')


class Administrador(db.Model):
    __tablename__ = 'administradores'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    correo = db.Column(db.String, unique=True, nullable=False)
    clave = db.Column(db.String, nullable=False)


class Deuda(db.Model):
    __tablename__ = 'deudas'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    capital = db.Column(db.Numeric, nullable=False)  # Monto sin interés
    interes = db.Column(db.Numeric)  # En porcentaje: ej. 5 = 5%
    plazo = db.Column(db.Integer,nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    deuda_total = db.Column(db.Numeric, nullable=False)  # Capital + intereses
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)
    finalizado = db.Column(db.Boolean, default=False)


class Pago(db.Model):
    __tablename__ = 'pagos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    deuda_id = db.Column(db.Integer, db.ForeignKey('deudas.id'), nullable=False)
    abono = db.Column(db.Numeric, nullable=False)
    interes_mora = db.Column(db.Numeric)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    deuda = db.relationship('Deuda', backref='pagos_relacion', lazy=True)
    
class Actividad(db.Model):
    __tablename__ = 'actividades'

    id = db.Column(db.Integer, primary_key=True)
    administrador_id = db.Column(db.Integer, db.ForeignKey('administradores.id'), nullable=False)
    accion = db.Column(db.String, nullable=False)  # 'crear', 'editar', 'eliminar', etc.
    descripcion = db.Column(db.Text)  # detalles de la acción
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    administrador = db.relationship('Administrador', backref='actividades', lazy=True)
