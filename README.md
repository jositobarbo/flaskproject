# Aplicación de Revenue Hotelero

Esta aplicación está desarrollada con **Flask** y permite gestionar la ocupación y las tarifas de un establecimiento hotelero. Incluye páginas para visualizar métricas de revenue, exportar datos y gestionar precios desde un calendario interactivo.

## Instalación de dependencias

Se recomienda usar un entorno virtual de Python. Una vez activado, instalar las dependencias ejecutando:

```bash
pip install -r requirements.txt
```

## Inicialización de la base de datos

Al iniciarse por primera vez, la aplicación crea automáticamente el archivo SQLite `ocupacion.db` y las tablas necesarias. No es necesario ejecutar scripts adicionales: basta con arrancar el servidor para que la base de datos se genere si no existe.

## Ejecución del servidor Flask

Utilice la interfaz de línea de comandos de Flask indicando el módulo de la aplicación:

```bash
FLASK_APP=main flask run
```

Tras ejecutarlo, podrá acceder a la aplicación en `http://127.0.0.1:5000/`.
