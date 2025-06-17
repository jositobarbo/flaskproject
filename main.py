from flask import Flask, render_template, request
import sqlite3
import openpyxl
from flask import send_file
from io import BytesIO
import matplotlib.pyplot as plt
import base64
import datetime
import os
import calendar
from datetime import datetime

app = Flask(__name__)

# Función que detecta la temporada según la fecha
def detectar_temporada(fecha):
    if '07-01' <= fecha[5:] <= '08-31':
        return 'alta'
    elif '04-01' <= fecha[5:] <= '06-30' or '09-01' <= fecha[5:] <= '10-31':
        return 'media'
    else:
        return 'baja'
    
@app.route('/')
def index():
    conn = sqlite3.connect('ocupacion.db')
    cursor = conn.cursor()

    cursor.execute("SELECT AVG(ocupacion), AVG(adr), AVG(revpar), MAX(fecha) FROM ocupacion_diaria")
    ocupacion_media, adr_media, revpar_media, ultima_fecha = cursor.fetchone()
    conn.close()

    return render_template(
        'index.html',
        ocupacion_media=round(ocupacion_media, 2),
        adr_media=round(adr_media, 2),
        revpar_media=round(revpar_media, 2),
        ultima_fecha=ultima_fecha
    )


@app.route('/ocupacion/', methods=['GET', 'POST'])
def ocupacion():
    conn = sqlite3.connect('ocupacion.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        desde = request.form.get('desde')
        hasta = request.form.get('hasta')
        cursor.execute("""
            SELECT fecha, ocupacion, adr, revpar
            FROM ocupacion_diaria
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha
        """, (desde, hasta))
    else:
        cursor.execute("SELECT fecha, ocupacion, adr, revpar FROM ocupacion_diaria ORDER BY fecha")

    datos = cursor.fetchall()
    conn.close()

    # Generar gráficos
    fechas = [fila[0] for fila in datos]
    ocupaciones = [fila[1] for fila in datos]
    ingresos = [(fila[1]/100) * fila[2] for fila in datos]
    ingresos_acumulados = []
    acumulado = 0
    for ingreso in ingresos:
        acumulado += ingreso
        ingresos_acumulados.append(acumulado)

    # Gráfico ocupación diaria
    fig1, ax1 = plt.subplots()
    ax1.bar(fechas, ocupaciones, color='skyblue')
    ax1.set_title('Ocupación Diaria')
    ax1.set_ylabel('%')
    ax1.tick_params(axis='x', rotation=45)
    buf1 = BytesIO()
    plt.tight_layout()
    plt.savefig(buf1, format='png')
    buf1.seek(0)
    ocupacion_img = base64.b64encode(buf1.read()).decode('utf-8')
    plt.close(fig1)

    # Gráfico ingresos acumulados
    fig2, ax2 = plt.subplots()
    ax2.plot(fechas, ingresos_acumulados, marker='o', color='green')
    ax2.set_title('Ingresos Acumulados')
    ax2.set_ylabel('Euros')
    ax2.tick_params(axis='x', rotation=45)
    buf2 = BytesIO()
    plt.tight_layout()
    plt.savefig(buf2, format='png')
    buf2.seek(0)
    ingresos_img = base64.b64encode(buf2.read()).decode('utf-8')
    plt.close(fig2)

    return render_template('ocupacion.html', datos=datos, ocupacion_img=ocupacion_img, ingresos_img=ingresos_img)

@app.route('/ocupacion/exportar/')
def exportar_ocupacion():
    conn = sqlite3.connect('ocupacion.db')
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, ocupacion, adr, revpar FROM ocupacion_diaria ORDER BY fecha")
    datos = cursor.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ocupación"
    ws.append(['Fecha', 'Ocupación (%)', 'ADR (€)', 'RevPAR (€)'])
    for fila in datos:
        ws.append(fila)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output, download_name="ocupacion.xlsx", as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/tarifas/')
def tarifas():
    return render_template('tarifas.html')

@app.route('/simulador/', methods=['GET', 'POST'])
def simulador():
    if request.method == 'POST':
        fecha_entrada = request.form.get('fecha_entrada')
        habitacion = request.form.get('habitacion')
        tarifa_tipo = request.form.get('tarifa_tipo')

        temporada = detectar_temporada(fecha_entrada)

        # Tarifa base según temporada
        if temporada == 'baja':
            base = 90
        elif temporada == 'media':
            base = 105
        else:
            base = 120

        # Ajustes según tipo de habitación
        if habitacion == 'economica':
            factor_hab = 0.85
        elif habitacion == 'estandar':
            factor_hab = 1.0
        elif habitacion == 'superior':
            factor_hab = 1.15
        else:  # suite
            factor_hab = 1.30

        # Ajuste por tipo de tarifa
        factor_tarifa = 0.90 if tarifa_tipo == 'no_reembolsable' else 1.0

        # Cálculo final
        tarifa = round(base * factor_hab * factor_tarifa, 2)

        return render_template(
            'resultado_simulador.html',
            fecha=fecha_entrada,
            temporada=temporada,
            tarifa=f"{tarifa} €",
            habitacion=habitacion.capitalize(),
            tarifa_tipo="No reembolsable" if tarifa_tipo == 'no_reembolsable' else "Reembolsable"
        )

    return render_template('simulador.html')

@app.route("/benchmark/", methods=["GET", "POST"])
def benchmark():
    conn = sqlite3.connect("ocupacion.db")
    cursor = conn.cursor()

    if request.method == "POST":
        nombre = request.form["nombre"]
        categoria = int(request.form["categoria"])
        puntuacion = float(request.form["puntuacion"])
        zona = request.form["zona"]
        habitaciones = int(request.form["habitaciones"])
        web = request.form["web"]
        notas = request.form["notas"]

        cursor.execute("""
            INSERT INTO compset (nombre, categoria, puntuacion, zona, habitaciones, web, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre, categoria, puntuacion, zona, habitaciones, web, notas))
        conn.commit()

    cursor.execute("SELECT * FROM compset")
    hoteles = cursor.fetchall()
    conn.close()

    return render_template("benchmark.html", hoteles=hoteles)


@app.route('/alertas/')
def alertas():
    return render_template('alertas.html')

@app.route('/reportes/')
def reportes():
    return render_template('reportes.html')

@app.route("/calendario/", methods=["GET", "POST"])
def calendario():
    from flask import request
    conn = sqlite3.connect("ocupacion.db")
    cursor = conn.cursor()

    hoy = datetime.today()
    year = hoy.year
    month = hoy.month

    if request.method == "POST":
        year = int(request.form["year"])
        month = int(request.form["month"])
        for key, value in request.form.items():
            if key.startswith("precio_") and value:
                fecha = key.split("_")[1]
                precio = float(value.replace(",", "."))
                cursor.execute("REPLACE INTO precios (fecha, precio) VALUES (?, ?)", (fecha, precio))
        conn.commit()

    temporadas = {
        "baja": [1, 2, 3, 4, 10, 11],
        "media": [5, 6, 9],
        "alta": [7, 8, 12]
    }

    cal = calendar.monthcalendar(year, month)

    if month in temporadas["baja"]:
        color = "rojo"
    elif month in temporadas["media"]:
        color = "amarillo"
    else:
        color = "verde"

    # Recuperar precios guardados
    cursor.execute("SELECT fecha, precio FROM precios")
    precios_dict = dict(cursor.fetchall())
    conn.close()

    return render_template("calendario.html",
                           cal=cal,
                           month=month,
                           year=year,
                           color=color,
                           precios=precios_dict)


# Crear base de datos solo si no existe
if not os.path.exists('ocupacion.db'):
    conn = sqlite3.connect('ocupacion.db')
    cursor = conn.cursor()

    cursor.execut

import sqlite3

def init_db():
    conn = sqlite3.connect("ocupacion.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precios (
            fecha TEXT PRIMARY KEY,
            precio REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()  # Llamar una vez al arrancar la app

def crear_tabla_compset():
    conn = sqlite3.connect("ocupacion.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            categoria INTEGER,
            puntuacion REAL,
            zona TEXT,
            habitaciones INTEGER,
            web TEXT,
            notas TEXT
        )
    """)
    conn.commit()
    conn.close()

crear_tabla_compset()

def convertir_a_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)  # <- esto evita los errores de GUI
    return image_base64
