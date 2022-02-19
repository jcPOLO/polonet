from app import db
from app.models import Base


# TODO: all
class Job(Base):
    status = db.Column(db.Integer, db.ForeignKey("status_code.id"), nullable=False) # 1:N
    started_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    finished_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False) # 1:N
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=False) # 1:N
    # TODO: text < JSON < new model ?
    output = db.Column(db.String(10000), nullable=False)


class StatusCode(Base):
    message = db.Column(db.String(20), nullable=False)
