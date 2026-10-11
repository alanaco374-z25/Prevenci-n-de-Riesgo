import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cambiar-esta-clave-en-produccion")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/contacto", methods=["POST"])
def contacto():
    # Leer y validar los campos enviados por el formulario
    nombre = (request.form.get("nombre") or "").strip()
    email = (request.form.get("email") or "").strip()
    servicio = (request.form.get("servicio") or "").strip()
    mensaje = (request.form.get("mensaje") or "").strip()

    if not all([nombre, email, servicio, mensaje]):
        flash("Completá todos los campos antes de enviar.", "error")
        return redirect(url_for("home"))

    api_key = os.environ.get("RESEND_API_KEY")
    correo_destino = os.environ.get("CORREO_DESTINO")
    correo_remitente = os.environ.get("RESEND_FROM_EMAIL")

    if not api_key or not correo_destino or not correo_remitente:
        app.logger.error(
            "Faltan variables de entorno: RESEND_API_KEY, CORREO_DESTINO o RESEND_FROM_EMAIL."
        )
        flash("No se pudo enviar el formulario en este momento. Intentá más tarde.", "error")
        return redirect(url_for("home"))

    asunto = f"Nuevo contacto desde la página: {nombre}"
    contenido = (
        "Recibiste un nuevo formulario de contacto.\n\n"
        f"Nombre: {nombre}\n"
        f"Correo: {email}\n"
        f"Servicio: {servicio}\n"
        f"Mensaje: {mensaje}\n"
    )

    try:
        respuesta = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": correo_remitente,
                "to": [correo_destino],
                "reply_to": email,
                "subject": asunto,
                "text": contenido,
            },
            timeout=15,
        )
        respuesta.raise_for_status()
    except requests.RequestException:
        app.logger.exception("No se pudo enviar el correo mediante Resend.")
        flash("No se pudo enviar el formulario. Revisá los datos e intentá nuevamente.", "error")
        return redirect(url_for("home"))

    flash("¡Gracias! Tus datos se enviaron correctamente.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
