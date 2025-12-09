from models import db
from datetime import datetime

class InventoryCount(db.Model):
    __tablename__ = "inventory_count"

    id = db.Column(db.Integer, primary_key=True)
    material_code = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    real_count = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)
