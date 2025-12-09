import uuid
from datetime import datetime
import pandas as pd

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify
)
from flask_login import login_required

# MODELOS
from models import db
from models.inventory import InventoryItem
from models.inventory_history import InventoryHistory
from models.inventory_count import InventoryCount

# UTILS
from utils.excel import (
    load_inventory_excel,
    sort_location_advanced,
    generate_discrepancies_excel,
)

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")

# =============================================================================
# 1. CARGAR INVENTARIO PRINCIPAL
# =============================================================================

@inventory_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_inventory():

    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            flash("Debes seleccionar un archivo Excel.", "warning")
            return redirect(url_for("inventory.upload_inventory"))

        try:
            df = load_inventory_excel(file)
        except Exception as e:
            flash(f"Error procesando el archivo: {str(e)}", "danger")
            return redirect(url_for("inventory.upload_inventory"))

        # Reemplazar inventario actual
        InventoryItem.query.delete()
        InventoryCount.query.delete()   # Limpia conteos anteriores
        db.session.commit()

        # Guardar nuevo inventario
        for _, row in df.iterrows():
            db.session.add(
                InventoryItem(
                    material_code=row["Código del Material"],
                    material_text=row["Texto breve de material"],
                    base_unit=row["Unidad de medida base"],
                    location=row["Ubicación"],
                    libre_utilizacion=row["Libre utilización"],
                )
            )

        # Guardar snapshot histórico
        snapshot_id = str(uuid.uuid4())
        snapshot_name = f"Inventario {datetime.now():%d/%m/%Y %H:%M}"

        for _, row in df.iterrows():
            db.session.add(
                InventoryHistory(
                    snapshot_id=snapshot_id,
                    snapshot_name=snapshot_name,
                    material_code=row["Código del Material"],
                    material_text=row["Texto breve de material"],
                    base_unit=row["Unidad de medida base"],
                    location=row["Ubicación"],
                    libre_utilizacion=row["Libre utilización"],
                )
            )

        db.session.commit()
        flash("Inventario cargado correctamente.", "success")
        return redirect(url_for("inventory.list_inventory"))

    return render_template("inventory/upload.html")

# =============================================================================
# 2. SUBIR HISTÓRICOS ANTIGUOS
# =============================================================================

@inventory_bp.route("/upload-history", methods=["GET", "POST"])
@login_required
def upload_inventory_history():

    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            flash("Debes seleccionar un archivo Excel.", "warning")
            return redirect(url_for("inventory.upload_inventory_history"))

        try:
            df = load_inventory_excel(file)
        except Exception as e:
            flash(f"Error procesando el archivo: {str(e)}", "danger")
            return redirect(url_for("inventory.upload_inventory_history"))

        snapshot_id = str(uuid.uuid4())
        snapshot_name = f"Histórico {datetime.now():%d/%m/%Y %H:%M}"

        for _, row in df.iterrows():
            db.session.add(
                InventoryHistory(
                    snapshot_id=snapshot_id,
                    snapshot_name=snapshot_name,
                    material_code=row["Código del Material"],
                    material_text=row["Texto breve de material"],
                    base_unit=row["Unidad de medida base"],
                    location=row["Ubicación"],
                    libre_utilizacion=row["Libre utilización"],
                )
            )

        db.session.commit()
        flash("Inventario histórico subido correctamente.", "success")
        return redirect(url_for("inventory.list_inventory"))

    return render_template("inventory/upload_history.html")


# =============================================================================
# 3. LISTA INVENTARIO
# =============================================================================

@inventory_bp.route("/list")
@login_required
def list_inventory():
    items = InventoryItem.query.all()
    items_sorted = sorted(items, key=lambda x: sort_location_advanced(x.location))
    return render_template("inventory/list.html", items=items_sorted)


# =============================================================================
# 4. CONTEO EN LÍNEA
# =============================================================================

@inventory_bp.route("/count")
@login_required
def count_inventory():
    items = InventoryItem.query.all()
    items_sorted = sorted(items, key=lambda x: sort_location_advanced(x.location))
    return render_template("inventory/count.html", items=items_sorted)


# =============================================================================
# 4.1 GUARDAR CONTEO REAL
# =============================================================================

@inventory_bp.route("/save-count", methods=["POST"])
@login_required
def save_count():
    try:
        data = request.get_json()

        if not isinstance(data, list):
            return jsonify({"success": False, "msg": "Formato inválido"}), 400

        # BORRAR conteo anterior
        InventoryCount.query.delete()

        for c in data:
            nuevo = InventoryCount(
                material_code=c["codigo"],
                location=c["ubicacion"],
                real_count=int(c["real"]),
                fecha=datetime.now()
            )
            db.session.add(nuevo)

        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        print("❌ ERROR SAVE COUNT:", e)
        return jsonify({"success": False}), 500


# =============================================================================
# 5. DASHBOARD DE INVENTARIO
# =============================================================================

@inventory_bp.route("/dashboard")
@login_required
def dashboard_inventory():

    items = InventoryItem.query.all()

    total_items = len(items)
    ubicaciones_unicas = len(set(i.location for i in items))

    criticos = sum(1 for i in items if i.libre_utilizacion <= 0)
    faltantes = sum(1 for i in items if 0 < i.libre_utilizacion < 5)

    estados = {"OK": 0, "FALTA": 0, "CRITICO": 0, "SOBRA": 0}

    for i in items:
        if i.libre_utilizacion == 0:
            estados["CRITICO"] += 1
        elif i.libre_utilizacion < 5:
            estados["FALTA"] += 1
        elif i.libre_utilizacion > 50:
            estados["SOBRA"] += 1
        else:
            estados["OK"] += 1

    ubicaciones = {}
    for i in items:
        ubicaciones[i.location] = ubicaciones.get(i.location, 0) + 1

    return render_template(
        "inventory/dashboard.html",
        total_items=total_items,
        ubicaciones_unicas=ubicaciones_unicas,
        criticos=criticos,
        faltantes=faltantes,
        estados=estados,
        ubicaciones_labels=list(ubicaciones.keys()),
        ubicaciones_counts=list(ubicaciones.values()),
        items=items
    )


# =============================================================================
# 6. DISCREPANCIAS (SUBIENDO ARCHIVO)
# =============================================================================

@inventory_bp.route("/discrepancies", methods=["GET", "POST"])
@login_required
def discrepancies():

    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            flash("Debe seleccionar un archivo.", "warning")
            return redirect(url_for("inventory.discrepancies"))

        try:
            df = load_inventory_excel(file)
        except Exception as e:
            flash(f"Error leyendo archivo: {str(e)}", "danger")
            return redirect(url_for("inventory.discrepancies"))

        df["Código del Material"] = df["Código del Material"].astype(str)
        df["Ubicación"] = df["Ubicación"].astype(str)

        # Inventario sistema
        sistema = pd.read_sql(
            db.session.query(
                InventoryItem.material_code.label("Código Material"),
                InventoryItem.material_text.label("Descripción"),
                InventoryItem.base_unit.label("Unidad"),
                InventoryItem.location.label("Ubicación"),
                db.func.sum(InventoryItem.libre_utilizacion).label("Stock sistema"),
            ).statement,
            db.session.bind
        )

        # Inventario contado
        conteo = df.groupby(
            ["Código del Material", "Ubicación"], as_index=False
        )["Libre utilización"].sum()

        conteo = conteo.rename(columns={
            "Código del Material": "Código Material",
            "Libre utilización": "Stock contado"
        })

        # mezclar
        merged = sistema.merge(conteo, on=["Código Material", "Ubicación"], how="outer")

        merged["Stock sistema"] = merged["Stock sistema"].fillna(0)
        merged["Stock contado"] = merged["Stock contado"].fillna(0)
        merged["Diferencia"] = merged["Stock contado"] - merged["Stock sistema"]

        estados = []
        for _, r in merged.iterrows():
            d = r["Diferencia"]
            if d == 0:
                estado = "OK"
            elif d < 0:
                estado = "CRÍTICO" if d <= -10 else "FALTA"
            else:
                estado = "SOBRA"
            estados.append(estado)

        merged["Estado"] = estados

        excel = generate_discrepancies_excel(merged)
        fname = f"discrepancias_{datetime.now():%Y%m%d_%H%M}.xlsx"

        return send_file(
            excel,
            as_attachment=True,
            download_name=fname,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    return render_template("inventory/discrepancies.html")


# =============================================================================
# 7. DISCREPANCIAS AUTOMÁTICAS (SIN ARCHIVO)
# =============================================================================

@inventory_bp.route("/discrepancies-auto")
@login_required
def discrepancies_auto():
    """
    Genera el Excel usando:
    - InventoryItem (sistema)
    - InventoryCount (conteo real)
    """

    sistema = pd.read_sql(
        db.session.query(
            InventoryItem.material_code.label("Código Material"),
            InventoryItem.material_text.label("Descripción"),
            InventoryItem.base_unit.label("Unidad"),
            InventoryItem.location.label("Ubicación"),
            db.func.sum(InventoryItem.libre_utilizacion).label("Stock sistema"),
        ).statement,
        db.session.bind
    )

    conteo = pd.read_sql(
        db.session.query(
            InventoryCount.material_code.label("Código Material"),
            InventoryCount.location.label("Ubicación"),
            db.func.sum(InventoryCount.real_count).label("Stock contado"),
        ).statement,
        db.session.bind
    )

    merged = sistema.merge(conteo, on=["Código Material", "Ubicación"], how="outer")

    merged["Stock sistema"] = merged["Stock sistema"].fillna(0)
    merged["Stock contado"] = merged["Stock contado"].fillna(0)
    merged["Diferencia"] = merged["Stock contado"] - merged["Stock sistema"]

    # Estados
    estados = []
    for _, r in merged.iterrows():
        diff = r["Diferencia"]
        if diff == 0:
            estado = "OK"
        elif diff < 0:
            estado = "CRÍTICO" if diff <= -10 else "FALTA"
        else:
            estado = "SOBRA"
        estados.append(estado)

    merged["Estado"] = estados

    # Exportar Excel
    excel = generate_discrepancies_excel(merged)
    fname = f"discrepancias_conteo_{datetime.now():%Y%m%d_%H%M}.xlsx"

    return send_file(
        excel,
        as_attachment=True,
        download_name=fname,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
