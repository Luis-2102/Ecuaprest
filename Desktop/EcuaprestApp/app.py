from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import os, io
from functools import wraps
from models import db, Cliente, Administrador, Documento, Deuda, Pago
from flask import jsonify
from config import Config

app = Flask(__name__)
app.secret_key = 'ecuaprest_secret_key'  


app.config.from_object(Config)  # 👈 Carga la configuración desde config.py
db.init_app(app)  # 👈 Aquí se enlaza Flask con SQLAlchemy


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

# Routes
@app.route('/')
def index():
    lista_clientes = Cliente.query.order_by(Cliente.id.desc()).limit(5).all()
    return render_template('index.html',clientes=lista_clientes)

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
    deuda_total = request.form['deuda_total']
    fecha = request.form['fecha']
    descripcion = request.form.get('descripcion', '')
    interes = request.form.get('interes') or 0
    interes_mora = request.form.get('interes_mora') or 0

    nueva_deuda = Deuda(
        cliente_id=cliente_id,
        deuda_total=deuda_total,
        fecha=datetime.strptime(fecha, "%Y-%m-%d"),
        descripcion=descripcion,
        interes=interes,
        interes_mora=interes_mora
    )
    db.session.add(nueva_deuda)
    db.session.commit()
    flash('Deuda agregada correctamente.', 'success')
    return redirect(url_for('clientes'))

@app.route('/pagar_deuda', methods=['POST'])
def pagar_deuda():
    cliente_id = request.form['cliente_id']
    abono = request.form['abono']
    fecha_pago = request.form.get('fecha_pago')

    # Puedes implementar lógica para encontrar la deuda activa del cliente
    deuda = Deuda.query.filter_by(cliente_id=cliente_id, finalizado=False).first()
    if not deuda:
        flash('No se encontró deuda activa para este cliente.', 'danger')
        return redirect(url_for('clientes'))

    nuevo_pago = Pago(
        cliente_id=cliente_id,
        deuda_id=deuda.id,
        abono=abono,
        fecha_pago=datetime.strptime(fecha_pago, "%Y-%m-%dT%H:%M") if fecha_pago else datetime.utcnow()
    )
    db.session.add(nuevo_pago)
    db.session.commit()
    flash('Pago registrado correctamente.', 'success')
    return redirect(url_for('clientes'))

@app.route('/editar_cliente/<int:cliente_id>', methods=['POST'])
@login_required
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    documento = Documento.query.filter_by(cliente_id=cliente_id).first()
    archivo = request.files.get('archivo')

    cliente.name = request.form['name']
    cliente.cedula = request.form['cedula']
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

    flash('Cliente actualizado correctamente.', 'success')
    return redirect(url_for('clientes'))

@app.route('/eliminar_cliente/<int:cliente_id>')
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    documento = Documento.query.filter_by(cliente_id=cliente_id).first()

    # Puedes implementar validaciones como: si tiene deudas activas, no permitir eliminar
    db.session.delete(documento)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado correctamente.', 'success')
    return redirect(url_for('clientes'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Se ha cerrado la sesión', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('pages/samples/dashboard.html')

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
    cuenta = request.args.get('cuenta', '')
    clientes = Cliente.query.filter(Cliente.numero_cuenta.ilike(f"%{cuenta}%")).all()

    data = [
        {
            'name': c.name,
            'cedula': c.cedula,
            'correo': c.correo,
            'numero_cuenta': c.numero_cuenta,
            'id': c.id
        }
        for c in clientes
    ]
    return jsonify(data)



# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Esto solo si necesitas crear tablas desde código
    app.run(debug=True)
