from app import db
from app.models import Base


# TODO: all
class Job(Base):
    status = db.Column(db.String(39))
    started_at = db.Column(db.DateTime, default=db.func.now())
    finished_at = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # 1:N
    inventory_id = db.Column(db.Integer, db.ForeignKey("user.id")) # 1:N
    output = db.Column(db.String(10000))
