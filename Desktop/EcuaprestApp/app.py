from datetime import datetime, timedelta
import humanize
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, Blueprint, jsonify
import os, io
from functools import wraps
from models import db, Cliente, Administrador, Documento, Deuda, Pago, Actividad
from config import Config
from decimal import Decimal
from sqlalchemy import func
import pytz
import locale
from dateutil.relativedelta import relativedelta

MAXIMO_DIAS_MORA = 30


api = Blueprint('api', __name__)
app = Flask(__name__)
app.secret_key = 'ecuaprest_secret_key'  

app.config.from_object(Config)  # 👈 Carga la configuración desde config.py
db.init_app(app)  # 👈 Aquí se enlaza Flask con SQLAlchemy
zona_horaria = pytz.timezone('America/Guayaquil')

@app.route('/verificar_cuenta/<numero_cuenta>')
def verificar_cuenta(numero_cuenta):
    existe = Cliente.query.filter_by(numero_cuenta=str(numero_cuenta)).first() is not None
    return jsonify({'existe': existe})

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def registrar_actividad(accion, descripcion):
    hora_local = datetime.now(zona_horaria)
    admin_id = session.get('user_id')
    nueva_actividad = Actividad(
        administrador_id=admin_id,
        accion=accion,
        descripcion=descripcion,
        fecha=hora_local
    )
    db.session.add(nueva_actividad)
    db.session.commit()
    
# Filtro personalizado
@app.template_filter('tiempo_relativo')
def tiempo_relativo(fecha):
    
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # En algunos sistemas puede ser 'es_ES' o 'es_EC'
    humanize.i18n.activate('es')
    hora_local = datetime.now(zona_horaria)

    if fecha.tzinfo is None:
        fecha = zona_horaria.localize(fecha)

    return humanize.naturaltime(hora_local - fecha)


# Routes
@app.route('/')
def index():
    lista_clientes = Cliente.query.order_by(Cliente.id.desc()).limit(5).all()
    actividades = Actividad.query.order_by(Actividad.fecha.desc()).all()
    return render_template('index.html',clientes=lista_clientes, actividad=actividades)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Administrador.query.filter_by(nombre=username, clave=password).first()

        if admin:
            session['user_id'] = admin.id
            session['admin_nombre'] = admin.nombre
            session['admin_correo'] = admin.correo
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Correo o clave incorrectos', 'danger')
    return render_template('login.html')


@app.route('/añadir_cliente', methods=['POST'])
@login_required
def añadir_cliente():
    name = request.form['name']
    cedula = request.form['cedula']
    contrato = request.form['contrato']
    numero_cuenta = str(request.form['numero_cuenta'])
    correo = request.form['correo']
    telefono = request.form['telefono']
    archivo = request.files['archivo']

    if Cliente.query.filter_by(numero_cuenta=numero_cuenta).first():
        flash('El número de cuenta ya existe. Por favor genera uno nuevo.', 'danger')
        return redirect(url_for('clientes'))

    nuevo_cliente = Cliente(
        name=name,
        cedula=cedula,
        contrato=contrato,
        numero_cuenta=numero_cuenta,
        correo=correo,
        telefono=telefono
    )
    db.session.add(nuevo_cliente)
    db.session.commit()
    
    if archivo and archivo.filename.endswith('.pdf'):
        documento = Documento(
            cliente_id=nuevo_cliente.id,
            archivo=archivo.read(),
            nombre_archivo=archivo.filename,
            tipo_archivo=archivo.mimetype
        )
        db.session.add(documento)
        db.session.commit()
        
    registrar_actividad(
        accion='Agrego cliente',
        descripcion=f"Se registro al cliente {name} con numero de cuenta: {numero_cuenta}"
    )
    flash('Cliente añadido correctamente', 'success')
    return redirect(url_for('clientes'))

@app.route('/ver_documento/<int:cliente_id>')
@login_required
def ver_documento(cliente_id):
    documento = Documento.query.filter_by(cliente_id=cliente_id).first()
    if documento:
        return send_file(
            io.BytesIO(documento.archivo),
            mimetype=documento.tipo_archivo,
            download_name=documento.nombre_archivo,
            as_attachment=False
        )
    flash('Documento no encontrado', 'warning')
    return redirect(url_for('clientes'))

@app.route('/agregar_deuda', methods=['POST'])
def agregar_deuda():
    cliente_id = request.form['cliente_id']
    capital = Decimal(request.form['deuda_total'])
    fecha = datetime.strptime(request.form['fecha'], "%Y-%m-%d").date()
    descripcion = request.form.get('descripcion', '')
    interes = Decimal(request.form.get('interes') or 0)
    plazo = int(request.form['plazo'])

    # Calcular montos de interés
    interes_monto = (capital * interes) / 100
    
    # Calcular fecha de vencimiento
    fecha_vencimiento = fecha + relativedelta(months=plazo)

    # Calcular deuda total (capital + interés normal)
    deuda_total = capital + interes_monto

    finalizado = bool(request.form.get('finalizado'))

    nueva_deuda = Deuda(
        cliente_id=cliente_id,
        capital=capital,
        interes=interes,
        deuda_total=deuda_total,
        fecha=fecha,
        fecha_vencimiento=fecha_vencimiento,
        plazo=plazo,
        descripcion=descripcion,
        finalizado=finalizado
    )

    db.session.add(nueva_deuda)
    db.session.commit()

    cliente = Cliente.query.get(cliente_id)
    registrar_actividad(
        accion='Agregó Deuda',
        descripcion=f"Se agregó una deuda de {deuda_total} USD al cliente {cliente.name} (Cuenta: {cliente.numero_cuenta})"
    )

    flash('Deuda agregada correctamente.', 'success')
    return redirect(url_for('clientes'))

@app.route('/pagar_deuda', methods=['POST'])
def pagar_deuda():
    cliente_id = request.form['cliente_id']
    abono = Decimal(request.form['abono'])
    fecha_pago = request.form.get('fecha_pago')

    deuda = Deuda.query.filter_by(cliente_id=cliente_id, finalizado=False).first()
    if not deuda:
        flash('No se encontró deuda activa para este cliente.', 'danger')
        return redirect(url_for('clientes'))

    fecha_pago_dt = datetime.strptime(fecha_pago, "%Y-%m-%dT%H:%M") if fecha_pago else datetime.utcnow()

    # Calcular días de retraso desde la fecha de vencimiento
    dias_retraso = (fecha_pago_dt.date() - deuda.fecha_vencimiento).days

    interes_mora_total = Decimal(0)

    if dias_retraso > 0:
        dias_retraso_aplicado = min(dias_retraso, MAXIMO_DIAS_MORA)
        interes_mora_total = (deuda.capital * Decimal(deuda.interes_mora or 0) / 100) * dias_retraso_aplicado
        deuda.deuda_total += interes_mora_total

    # Registrar el nuevo pago
    nuevo_pago = Pago(
        cliente_id=cliente_id,
        deuda_id=deuda.id,
        abono=abono,
        interes_mora=interes_mora_total,
        fecha_pago=fecha_pago_dt
    )
    db.session.add(nuevo_pago)

    # Restar el abono del total de la deuda
    deuda.deuda_total -= abono

    # Marcar como finalizada si el total es cero o si se marcó manualmente
    if request.form.get('finalizado') or deuda.deuda_total <= 0:
        deuda.finalizado = True
        deuda.deuda_total = max(deuda.deuda_total, 0)  # Evitar negativos

    db.session.commit()

    cliente = Cliente.query.get(cliente_id)
    registrar_actividad(
        accion='Agregó Pago',
        descripcion=f"Se agregó un pago de {abono} USD al cliente {cliente.name} (Cuenta: {cliente.numero_cuenta})"
    )

    flash('Pago registrado correctamente.', 'success')
    return redirect(url_for('comprobante_pago', pago_id=nuevo_pago.id))



@app.route('/editar_cliente/<int:cliente_id>', methods=['POST'])
@login_required
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    documento = Documento.query.filter_by(cliente_id=cliente_id).first()
    archivo = request.files.get('archivo')

    cliente.name = request.form['name']
    cliente.cedula = request.form['cedula']
    cliente.contrato = request.form['contrato']
    cliente.correo = request.form['correo']
    cliente.numero_cuenta = request.form['numero_cuenta']
    cliente.telefono = request.form['telefono']

    # Guardar cambios del cliente
    db.session.commit()

    # Si se sube un nuevo documento
    if archivo and archivo.filename.endswith('.pdf'):
        if documento:
            # Si ya existe documento, actualizamos
            documento.archivo = archivo.read()
            documento.nombre_archivo = archivo.filename
            documento.tipo_archivo = archivo.mimetype
        else:
            # Si no existe, lo creamos
            nuevo_documento = Documento(
                cliente_id=cliente.id,
                archivo=archivo.read(),
                nombre_archivo=archivo.filename,
                tipo_archivo=archivo.mimetype
            )
            db.session.add(nuevo_documento)
        db.session.commit()
        
    registrar_actividad(
        accion='Edito cliente',
        descripcion=f"Se edito la informacion del cliente {cliente.name} con numero de cuenta: {cliente.numero_cuenta}"
    )

    flash('Cliente actualizado correctamente.', 'success')
    return redirect(url_for('clientes'))

@app.route('/eliminar_cliente/<int:cliente_id>')
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    
    # Eliminar los documentos relacionados con el cliente
    documentos = Documento.query.filter_by(cliente_id=cliente_id).all()
    for documento in documentos:
        db.session.delete(documento)
    
    # Eliminar las deudas relacionadas con el cliente
    deudas = Deuda.query.filter_by(cliente_id=cliente_id).all()
    for deuda in deudas:
        db.session.delete(deuda)
    
    # Eliminar los pagos relacionados con el cliente
    pagos = Pago.query.filter_by(cliente_id=cliente_id).all()
    for pago in pagos:
        db.session.delete(pago)
    
    # Eliminar el cliente
    db.session.delete(cliente)
    db.session.commit()
    
    registrar_actividad(
        accion='Elimino cliente',
        descripcion=f"Se elimino al cliente {cliente.name} con numero de cuenta: {cliente.numero_cuenta}"
    )
    
    flash('Cliente eliminado correctamente.', 'success')
    return redirect(url_for('clientes'))

@app.route('/api/pagos-por-dia', methods=['GET'])
def pagos_por_dia():
    # Obtener fecha actual
    hoy = datetime.utcnow()
    
    # Calcular inicio de esta semana (domingo)
    inicio_esta_semana = hoy - timedelta(days=hoy.weekday() + 1)
    inicio_esta_semana = inicio_esta_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calcular inicio de semana pasada
    inicio_semana_pasada = inicio_esta_semana - timedelta(days=7)
    
    # Obtener datos de esta semana agrupados por día
    pagos_esta_semana = db.session.query(
        func.sum(Pago.abono),
        func.extract('dow', Pago.fecha_pago)
    ).filter(
        Pago.fecha_pago >= inicio_esta_semana,
        Pago.fecha_pago < inicio_esta_semana + timedelta(days=7)
    ).group_by(
        func.extract('dow', Pago.fecha_pago)
    ).all()
    
    # Obtener datos de semana pasada agrupados por día
    pagos_semana_pasada = db.session.query(
        func.sum(Pago.abono),
        func.extract('dow', Pago.fecha_pago)
    ).filter(
        Pago.fecha_pago >= inicio_semana_pasada,
        Pago.fecha_pago < inicio_esta_semana
    ).group_by(
        func.extract('dow', Pago.fecha_pago)
    ).all()
    
    # Inicializar arrays para los 7 días de la semana
    datos_esta_semana = [0, 0, 0, 0, 0, 0, 0]
    datos_semana_pasada = [0, 0, 0, 0, 0, 0, 0]
    
    # Llenar datos de esta semana
    for suma, dia in pagos_esta_semana:
        dia_idx = int(dia)
        datos_esta_semana[dia_idx] = float(suma) if suma else 0
    
    # Llenar datos de semana pasada
    for suma, dia in pagos_semana_pasada:
        dia_idx = int(dia)
        datos_semana_pasada[dia_idx] = float(suma) if suma else 0
    
    return jsonify({
        'thisWeek': datos_esta_semana,
        'lastWeek': datos_semana_pasada
    })

@app.route('/logout')
def logout():
    session.clear()
    flash('Se ha cerrado la sesión', 'info')
    return redirect(url_for('login'))

@app.route('/amortizazion')
@login_required
def amortizacion():
    return render_template('Amortizacion.html')

# Sample routes for different sections based on your directory structure
@app.route('/charts')
@login_required
def charts():
    return render_template('pages/charts/index.html')

@app.route('/forms')
@login_required
def forms():
    return render_template('pages/forms/index.html')

@app.route('/tables')
@login_required
def tables():
    return render_template('pages/tables/index.html')

@app.route('/documentation')
def documentation():
    return render_template('pages/documentation/index.html')

@app.route('/Clientes')
@login_required
def clientes():
    lista_clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=lista_clientes)

@app.route('/buscar_clientes')
@login_required
def buscar_clientes():
    contrato = request.args.get('contrato', '')
    clientes = Cliente.query.filter(Cliente.contrato.ilike(f"%{contrato}%")).all()

    data = []
    for c in clientes:
        # Suma las deudas que no estén finalizadas
        deuda_total = sum(float(d.deuda_total) for d in c.deudas if not d.finalizado)
        # Tomamos la primera deuda no finalizada (puedes ajustar la lógica según lo que necesites)
        deuda_no_finalizada = next((d for d in c.deudas if not d.finalizado), None)

        if deuda_no_finalizada:
            deuda_fecha = deuda_no_finalizada.fecha.strftime("%Y-%m-%d")
            fecha_vencimiento = deuda_no_finalizada.fecha_vencimiento.strftime("%Y-%m-%d")
            pagos_relacion_length = len(deuda_no_finalizada.pagos_relacion)
        else:
            deuda_fecha = fecha_vencimiento = pagos_relacion_length = None

        data.append({
            'name': c.name,
            'cedula': c.cedula,
            'correo': c.correo,
            'contrato': c.contrato,
            'numero_cuenta': c.numero_cuenta,
            'telefono': c.telefono,
            'id': c.id,
            'deuda': deuda_total,  # El total de deuda no finalizada
            'deuda_fecha': deuda_fecha,
            'deuda_vencimiento': fecha_vencimiento,
            'deuda_pagos': pagos_relacion_length,
        })

    return jsonify(data)

@app.route('/buscar-cliente/<contrato>')
def buscar_cliente(contrato):
    cliente = Cliente.query.filter_by(contrato=contrato).first()
    if cliente:
        return jsonify({
            'name': cliente.name,
            'cedula': cliente.cedula
        })
    return jsonify({'error': 'Cliente no encontrado'}), 404

@app.route('/comprobante_pago/<int:pago_id>')
@login_required
def comprobante_pago(pago_id):
    pago = Pago.query.get_or_404(pago_id)
    cliente = pago.cliente
    deuda = pago.deuda

    return render_template('comprobante_pago.html', pago=pago, cliente=cliente, deuda=deuda)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Esto solo si necesitas crear tablas desde código
    app.run(debug=True)
