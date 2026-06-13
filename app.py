from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_mysqldb import MySQL
from reportlab.pdfgen import canvas
from io import BytesIO 
from flask import flash

app = Flask(__name__) 
app.secret_key = 'sistema_contable_secret'

# CONFIG MYSQL
app.config['MYSQL_HOST'] = 'acela.proxy.rlwy.net'
app.config['MYSQL_PORT'] = 28307
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'WkSguxiYFsIbRxRrzsKnImlmSayqJFgx'
app.config['MYSQL_DB'] = 'railway'

mysql = MySQL(app)

# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        correo = request.form['correo']
        password = request.form['password']

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT *
            FROM usuarios
            WHERE correo=%s
            AND password=%s
        """, (correo, password))

        usuario = cursor.fetchone()

        cursor.close()

        if usuario:

            session['usuario'] = usuario[1]
            session['correo'] = usuario[2]

            return redirect('/dashboard')

        else:
            return "Usuario o contraseña incorrecta"

    return render_template('login.html')

# CERRAR SESIÓN
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    # TOTAL INGRESOS
    cursor.execute("""
        SELECT IFNULL(SUM(monto), 0)
        FROM ingresos
    """)
    total_ingresos = cursor.fetchone()[0]

    # TOTAL EGRESOS
    cursor.execute("""
        SELECT IFNULL(SUM(monto), 0)
        FROM egresos
    """)
    total_egresos = cursor.fetchone()[0]

    # TOTAL VENTAS
    cursor.execute("""
        SELECT IFNULL(SUM(total), 0)
        FROM ventas
    """)
    total_ventas = cursor.fetchone()[0]

    # TOTAL COMPRAS
    cursor.execute("""
        SELECT IFNULL(SUM(total), 0)
        FROM compras
    """)
    total_compras = cursor.fetchone()[0]

    cursor.close()

    # BALANCE GENERAL
    balance = total_ingresos - total_egresos


    return render_template(
    'dashboard.html',
    ingresos=total_ingresos,
    egresos=total_egresos,
    ventas=total_ventas,
    compras=total_compras,
    usuario=session['usuario'],
    correo=session['correo']
)

# CATÁLOGO DE CUENTAS
@app.route('/catalogo', methods=['GET', 'POST'])
def catalogo():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        codigo = request.form['codigo']
        nombre = request.form['nombre']
        tipo = request.form['tipo']

        cursor.execute("""
            INSERT INTO catalogo_cuentas
            (codigo, nombre_cuenta, tipo)
            VALUES (%s, %s, %s)
        """, (codigo, nombre, tipo))

        mysql.connection.commit()

        # ALERTA DE GUARDADO
        flash('Cuenta registrada correctamente', 'success')

        return redirect('/catalogo')

    cursor.execute("""
        SELECT * FROM catalogo_cuentas
    """)

    cuentas = cursor.fetchall()

    cursor.close()

    return render_template(
        'catalogo.html',
        cuentas=cuentas
    )


# ELIMINAR CUENTA
@app.route('/eliminar_cuenta/<int:id>')
def eliminar_cuenta(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM catalogo_cuentas
        WHERE id_cuenta = %s
    """, (id,))

    mysql.connection.commit()

    cursor.close()

    return redirect('/catalogo')

# EDITAR CUENTA
@app.route('/editar_cuenta/<int:id>', methods=['GET', 'POST'])
def editar_cuenta(id):

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        codigo = request.form['codigo']
        nombre = request.form['nombre']
        tipo = request.form['tipo']

        cursor.execute("""
            UPDATE catalogo_cuentas
            SET codigo=%s,
            nombre_cuenta=%s,
            tipo=%s
            WHERE id_cuenta=%s
        """, (codigo, nombre, tipo, id))

        mysql.connection.commit()

        return redirect('/catalogo')

    cursor.execute("""
        SELECT * FROM catalogo_cuentas
        WHERE id_cuenta = %s
    """, (id,))

    cuenta = cursor.fetchone()

    cursor.close()

    return render_template(
        'editar_cuenta.html',
        cuenta=cuenta
    )

# PDF CATÁLOGO DE CUENTAS
@app.route('/pdf_catalogo')
def pdf_catalogo():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM catalogo_cuentas
    """)

    cuentas = cursor.fetchall()

    cursor.close()

    buffer = BytesIO()

    p = canvas.Canvas(buffer)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "Catálogo de Cuentas")

    y = 750

    p.setFont("Helvetica", 11)

    for cuenta in cuentas:

        texto = (
            f"ID: {cuenta[0]} | "
            f"Código: {cuenta[1]} | "
            f"Cuenta: {cuenta[2]} | "
            f"Tipo: {cuenta[3]}"
        )

        p.drawString(50, y, texto)

        y -= 20

    p.save()

    buffer.seek(0)

    response = make_response(buffer.read())

    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = (
        'inline; filename=catalogo_cuentas.pdf'
    )

    return response

# INGRESOS
@app.route('/ingresos', methods=['GET', 'POST'])
def ingresos():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        fecha = request.form['fecha']
        descripcion = request.form['descripcion']
        monto = request.form['monto']

        cursor.execute("""
            INSERT INTO ingresos
            (fecha, descripcion, monto)
            VALUES (%s, %s, %s)
        """, (fecha, descripcion, monto))

        mysql.connection.commit()

        # ALERTA DE GUARDADO
        flash('Ingreso registrado correctamente', 'success')

        return redirect('/ingresos')

    cursor.execute("""
        SELECT * FROM ingresos
    """)

    ingresos = cursor.fetchall()

    cursor.close()

    return render_template(
        'ingresos.html',
        ingresos=ingresos
    )


# ELIMINAR INGRESO
@app.route('/eliminar_ingreso/<int:id>')
def eliminar_ingreso(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM ingresos
        WHERE id_ingreso = %s
    """, (id,))

    mysql.connection.commit()

    cursor.close()

    return redirect('/ingresos')

# EGRESOS
@app.route('/egresos', methods=['GET', 'POST'])
def egresos():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        fecha = request.form['fecha']
        descripcion = request.form['descripcion']
        monto = request.form['monto']

        cursor.execute("""
            INSERT INTO egresos
            (fecha, descripcion, monto)
            VALUES (%s, %s, %s)
        """, (fecha, descripcion, monto))

        mysql.connection.commit()

        # ALERTA DE GUARDADO
        flash('Egreso registrado correctamente', 'success')

        return redirect('/egresos')

    cursor.execute("""
        SELECT * FROM egresos
    """)

    egresos = cursor.fetchall()

    cursor.close()

    return render_template(
        'egresos.html',
        egresos=egresos
    )


# ELIMINAR EGRESO
@app.route('/eliminar_egreso/<int:id>')
def eliminar_egreso(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM egresos
        WHERE id_egreso = %s
    """, (id,))

    mysql.connection.commit()

    cursor.close()

    return redirect('/egresos')

# LIBRO DE VENTAS
@app.route('/ventas', methods=['GET', 'POST'])
def ventas():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        fecha = request.form['fecha']
        cliente = request.form['cliente']
        factura = request.form['factura']
        total = request.form['total']

        cursor.execute("""
            INSERT INTO ventas
            (fecha, cliente, factura, total)
            VALUES (%s, %s, %s, %s)
        """, (fecha, cliente, factura, total))

        mysql.connection.commit()

        # ALERTA DE GUARDADO
        flash('Venta registrada correctamente', 'success')

        return redirect('/ventas')

    cursor.execute("""
        SELECT * FROM ventas
    """)

    ventas = cursor.fetchall()

    cursor.close()

    return render_template(
        'ventas.html',
        ventas=ventas
    )


# ELIMINAR VENTA
@app.route('/eliminar_venta/<int:id>')
def eliminar_venta(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM ventas
        WHERE id_venta = %s
    """, (id,))

    mysql.connection.commit()

    cursor.close()

    return redirect('/ventas')

# LIBRO DE COMPRAS
@app.route('/compras', methods=['GET', 'POST'])
def compras():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        fecha = request.form['fecha']
        proveedor = request.form['proveedor']
        factura = request.form['factura']
        total = request.form['total']

        cursor.execute("""
            INSERT INTO compras
            (fecha, proveedor, factura, total)
            VALUES (%s, %s, %s, %s)
        """, (fecha, proveedor, factura, total))

        mysql.connection.commit()

        # ALERTA DE GUARDADO
        flash('Compra registrada correctamente', 'success')

        return redirect('/compras')

    cursor.execute("""
        SELECT * FROM compras
    """)

    compras = cursor.fetchall()

    cursor.close()

    return render_template(
        'compras.html',
        compras=compras
    )


# ELIMINAR COMPRA
@app.route('/eliminar_compra/<int:id>')
def eliminar_compra(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM compras
        WHERE id_compra = %s
    """, (id,))

    mysql.connection.commit()

    cursor.close()

    return redirect('/compras')

# LIBRO DIARIO
@app.route('/libro_diario', methods=['GET', 'POST'])
def libro_diario():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        fecha = request.form['fecha']
        cuenta = request.form['cuenta']
        debe = request.form['debe']
        haber = request.form['haber']
        descripcion = request.form['descripcion']

        cursor.execute("""
            INSERT INTO libro_diario
            (fecha, cuenta, debe, haber, descripcion)
            VALUES (%s, %s, %s, %s, %s)
        """, (fecha, cuenta, debe, haber, descripcion))

        mysql.connection.commit()

        # ALERTA DE GUARDADO
        flash('Asiento registrado correctamente', 'success')

        return redirect('/libro_diario')

    cursor.execute("""
        SELECT * FROM libro_diario
    """)

    diarios = cursor.fetchall()

    cursor.close()

    return render_template(
        'libro_diario.html',
        diarios=diarios
    )


# ELIMINAR LIBRO DIARIO
@app.route('/eliminar_diario/<int:id>')
def eliminar_diario(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        DELETE FROM libro_diario
        WHERE id_diario = %s
    """, (id,))

    mysql.connection.commit()

    cursor.close()

    return redirect('/libro_diario')

# LIBRO MAYOR
@app.route('/libro_mayor', methods=['GET', 'POST'])
def libro_mayor():

    if 'usuario' not in session:
        return redirect('/')

    cursor = mysql.connection.cursor()

    mayores = []

    if request.method == 'POST':

        cuenta = request.form['cuenta']

        cursor.execute("""
            SELECT *
            FROM libro_diario
            WHERE cuenta = %s
        """, (cuenta,))

        mayores = cursor.fetchall()

    cursor.close()

    return render_template(
        'libro_mayor.html',
        mayores=mayores
    )


if __name__ == '__main__':
    app.run(debug=True)

