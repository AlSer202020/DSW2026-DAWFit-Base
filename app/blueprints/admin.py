import os
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db, login_manager, Actividad
from app.forms import ActividadForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
def rediregir_login():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.es_monitor:
        abort(403)

@admin_bp.route("/actividad/nueva", methods=["GET", "POST"])
def crear_actividad():
    form = ActividadForm()
    if form.validate_on_submit():
        nombre_imagen = None
        if form.archivo_imagen.data:
            archivo = form.archivo_imagen.data
            nombre_imagen = secure_filename(form.deporte.data.lower()+"_"+archivo.filename)
            carpeta_subidas = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(carpeta_subidas, exist_ok=True)
            archivo.save(os.path.join(carpeta_subidas, nombre_imagen))
        nueva_act = Actividad(
            nombre=form.nombre.data,
            deporte=form.deporte.data,
            imagen=nombre_imagen,
            plazas_libres=form.plazas_libres.data,
            cuota=form.cuota.data
        )
        db.session.add(nueva_act)
        db.session.commit()
        flash("Actividad creada correctamente.", "exito")
        return redirect(url_for("public.mostrar_actividades"))
    
    return render_template(
        "actividad_form.html", form=form, titulo="Nueva Actividad Deportiva"
    )


@admin_bp.route("/actividad/<int:act_id>/editar", methods=["GET", "POST"])
def editar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    form = ActividadForm(obj=actividad)
    form.id_actual = actividad.id 

    if form.validate_on_submit():
        actividad.nombre = form.nombre.data
        actividad.deporte = form.deporte.data
        actividad.plazas_libres = form.plazas_libres.data
        actividad.cuota = form.cuota.data

        if form.archivo_imagen.data:
            archivo = form.archivo_imagen.data
            nombre_imagen = secure_filename(form.deporte.data.lower()+"_"+archivo.filename)            
            carpeta_subidas = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(carpeta_subidas, exist_ok=True)
            archivo.save(os.path.join(carpeta_subidas, nombre_imagen))

            if actividad.imagen and actividad.imagen != nombre_imagen:
                ruta_antigua = os.path.join(carpeta_subidas, actividad.imagen)
                if os.path.exists(ruta_antigua):
                    os.remove(ruta_antigua)

            actividad.imagen = nombre_imagen

        db.session.commit()
        flash("Producto actualizado con éxito.", "exito")
        return redirect(url_for("public.mostrar_actividades"))

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):
    act = db.get_or_404(Actividad, act_id)
    if act.plazas_libres == 0:
        flash("No se puede eliminar producto con 0 plazas libres", "error")
    else: 
        db.session.delete(act)
        db.session.commit()
        flash(f"Producto '{act.nombre}' eliminado.", "info")
    return redirect(url_for("public.mostrar_actividades"))
