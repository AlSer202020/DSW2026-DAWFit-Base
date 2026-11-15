from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from app.models import db, Actividad

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return redirect(url_for("public.mostrar_actividades"))




@public_bp.route("/actividades")
def mostrar_actividades():

    busqueda  = request.args.get("busqueda")
    solo_con_plazas  = request.args.get("solo_con_plazas")
    consulta = Actividad.query

    if busqueda is not None and solo_con_plazas == "on":
       actividades =  consulta.filter(Actividad.nombre.contains(busqueda)).filter(Actividad.plazas_libres > 0)
    elif busqueda is not None :
        actividades =  consulta.filter(Actividad.nombre.contains(busqueda))
    elif solo_con_plazas == "on":
        actividades =  consulta.filter(Actividad.plazas_libres > 0)
    else:
        actividades = consulta.all()

    deporte_fav = request.cookies.get("deporte_fav")

    return render_template(
        "catalogo.html",
        lista_actividades=actividades,
        deporte_fav=deporte_fav,
    )


@public_bp.route("/actividad/<int:act_id>")
def ver_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    return render_template("actividad_detalle.html", actividad=actividad)


@public_bp.route("/preferencia/<string:deporte>")
def guardar_preferencia(deporte):
    resp = make_response(redirect(url_for("public.mostrar_actividades")))
    resp.set_cookie("deporte_fav", deporte, max_age=60*60*24*15, samesite="Lax", httponly=True)
    return resp


@public_bp.route("/limpiar-preferencia")
def limpiar_preferencia():
    resp = make_response(redirect(url_for("public.mostrar_actividades")))
    resp.delete_cookie("deporte_fav")
    return resp


@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    reservas = session.get("reservas", [])
    if actividad.plazas_libres == 0:
        flash("No quedan plazas libres para esta actividad", "error")
        return redirect(url_for("public.mostrar_actividades"))
    if len(reservas) >= 3:
        flash("No se puede estar apuntado a mas de 3 actividades", "error")
        return redirect(url_for("public.mostrar_actividades"))
    if actividad.id in reservas:
        flash("Esta actividad ya esta en reservas", "error")
        return redirect(url_for("public.mostrar_actividades"))
    reservas.append(actividad.id)
    session["reservas"] = reservas
    session.permanent = True
    session.modified=True
    flash("Se apunto a la actividad correctamente", "exito")
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/reservas")
@login_required
def ver_reservas():
    
    ids = session.get("reservas", [])
    actividades = Actividad.query.filter(Actividad.id.in_(ids)).all()

    total_sin_descuento=0.0
    for act in actividades:
        total_sin_descuento+=act.cuota

    if len(actividades) == 3:
        descuento_aplicado=True
        descuento = total_sin_descuento / 100.0 * 20.0
        total_final = total_sin_descuento - descuento
    else:
        descuento_aplicado=False
        total_final = total_sin_descuento
    
    return render_template(
        "reservas.html",
        actividades=actividades,
        total_sin_descuento=total_sin_descuento,
        descuento_aplicado=descuento_aplicado,
        total_final=total_final,
    )


@public_bp.route("/reservas/cancelar/<int:act_id>", methods=["POST"])
@login_required
def cancelar_reserva(act_id):
    reservas = session.get("reservas", [])
    if act_id in reservas:
        reservas.remove(act_id)
        session.modified=True
        flash("Actividad eliminada de reservas", "info")
    else:
        flash("Actividad no estaba reservada", "error")
    return redirect(url_for("public.ver_reservas"))


@public_bp.route("/reservas/confirmar", methods=["POST"])
@login_required
def confirmar_reservas():
    reservas = session.get("reservas", [])
    
    ids = session.get("reservas", [])
    actividades = Actividad.query.filter(Actividad.id.in_(ids)).all()
    for actividad in actividades:
        actividad.plazas_libres-=1
    db.session.commit()
    session.pop("reservas", None)
    flash("Se apunto a las actividades con exito")
    return redirect(url_for("public.mostrar_actividades"))

