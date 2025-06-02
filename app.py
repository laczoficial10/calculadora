from flask import Flask, request, render_template_string, Response, send_file
from openpyxl import Workbook
import csv
import io
import tempfile

app = Flask(__name__)

html_template = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Calculadoras de Descuento 50%</title>
</head>
<body style="font-family:sans-serif;max-width:800px;margin:30px auto;">
  <h1>Calculadoras 50%</h1>

  <!-- Sección 1 -->
  <h2>1. Calculadora formato: número-valor.00-4431</h2>
  <form method="POST" action="/formato1">
    <textarea name="entrada" rows="10" cols="80" placeholder="3108900530,35943\n3108900532,55099">{{ entrada1 }}</textarea><br><br>
    <button type="submit">Calcular</button>
  </form>

  {% if resultado1 %}
    <h3>Resultado:</h3>
    <textarea rows="10" cols="80">{{ resultado1 }}</textarea><br><br>
    <form method="POST" action="/descargar_txt">
      <input type="hidden" name="contenido" value="{{ resultado1 | replace('\n', '&#10;') }}">
      <button type="submit">Descargar TXT</button>
    </form>
  {% endif %}

  <hr>

  <!-- Sección 2 -->
  <h2>2. Calculadora para tabla tipo Excel (.xlsx)</h2>
  <form method="POST" action="/formato2">
    <textarea name="entrada" rows="10" cols="80" placeholder="3214789874,50000\n3001234567,75000">{{ entrada2 }}</textarea><br><br>
    <button type="submit">Procesar</button>
  </form>

  {% if resultado2 %}
    <h3>Vista previa:</h3>
    <table border="1" cellpadding="5" cellspacing="0">
      <thead>
        <tr>
          <th>Número completo</th>
          <th>Deuda original</th>
          <th>Deuda con 50%</th>
          <th>Últimos 4 dígitos</th>
        </tr>
      </thead>
      <tbody>
        {% for row in resultado2 %}
        <tr>
          <td>{{ row[0] }}</td>
          <td>{{ row[1] }}</td>
          <td>{{ row[2] }}</td>
          <td>{{ row[3] }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table><br>
    <form method="POST" action="/descargar_csv">
      <input type="hidden" name="contenido" value="{{ csv_data }}">
      <button type="submit">Descargar Excel (.xlsx)</button>
    </form>
  {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(html_template, entrada1='', entrada2='', resultado1=None, resultado2=None)

@app.route('/formato1', methods=['POST'])
def formato1():
    texto = request.form.get('entrada', '')
    resultado = []

    for linea in texto.strip().splitlines():
        partes = linea.strip().split(',')
        if len(partes) == 2:
            numero, monto = partes
            try:
                monto = float(monto.replace('.', '').replace(',', '.'))
                mitad = round(monto * 0.5)
                mitad_formateado = f"{mitad:,.0f}".replace(",", ".") + ".00"
                resultado.append(f"{numero}-{mitad_formateado}-4431")
            except ValueError:
                resultado.append(f"{linea}-ERROR")
        else:
            resultado.append(f"{linea}-ERROR")

    return render_template_string(html_template,
                                  entrada1=texto,
                                  resultado1='\n'.join(resultado),
                                  entrada2='',
                                  resultado2=None)

@app.route('/descargar_txt', methods=['POST'])
def descargar_txt():
    contenido = request.form.get('contenido', '')
    return Response(
        contenido,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment;filename=resultado.txt'}
    )

@app.route('/formato2', methods=['POST'])
def formato2():
    texto = request.form.get('entrada', '')
    resultado = []
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Número completo", "Deuda original", "Deuda con 50%", "Últimos 4 dígitos"])

    for linea in texto.strip().splitlines():
        partes = linea.strip().split(',')
        if len(partes) == 2:
            numero, monto = partes
            try:
                monto = float(monto.replace('.', '').replace(',', '.'))
                numero_completo = '57' + numero.strip()
                deuda_original = f"{monto:,.3f}".replace(",", ".")
                deuda_50 = f"{(monto * 0.5):,.3f}".replace(",", ".")
                ultimos4 = numero[-4:]
                resultado.append([numero_completo, deuda_original, deuda_50, ultimos4])
                writer.writerow([numero_completo, deuda_original, deuda_50, ultimos4])
            except ValueError:
                resultado.append([numero, "ERROR", "ERROR", "----"])
                writer.writerow([numero, "ERROR", "ERROR", "----"])

    return render_template_string(html_template,
                                  entrada2=texto,
                                  resultado2=resultado,
                                  csv_data=output.getvalue(),
                                  entrada1='',
                                  resultado1=None)

@app.route('/descargar_csv', methods=['POST'])
def descargar_csv():
    contenido = request.form.get('contenido', '')
    lines = contenido.strip().splitlines()

    wb = Workbook()
    ws = wb.active
    ws.title = "Resultados"

    for line in lines:
        ws.append(line.split(','))

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    tmp.close()

    return send_file(tmp.name, as_attachment=True, download_name="resultado.xlsx")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
