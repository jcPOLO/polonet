import json
from typing import Dict, List
from app import db
from app import ma
from flask_login import current_user
from marshmallow import (
    ValidationError,
    post_dump,
    post_load,
    pre_dump,
    pre_load,
    validates,
    fields,
)
from app.core.models.device import Device as NornirDevice
from app.core.exceptions import ValidationException
from app.job.models import Job, StatusCode
from app.auth.models import User
from slugify import slugify
from datetime import datetime


class JobSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Job
        include_relationships = True
        include_fk = True
        fields = (
            "id",
            "status",
            "started_at",
            "finished_at",
            "user_id",
            "inventory_id",
            "output",
        )

    id = ma.auto_field()
    status = ma.auto_field()
    started_at = fields.DateTime("%Y/%m/%d %H:%M:%S")
    finished_at = fields.DateTime("%Y/%m/%d %H:%M:%S")
    user_id = ma.auto_field()
    inventory_id = ma.auto_field()
    output = ma.auto_field()

    # @pre_dump
    # def job_pre_dump(self, data, **kwargs):
    #     print(data.started_at)
    #     data.started_at = data.started_at.strftime("%b %d %Y %H:%M:%S")
    #     data.finished_at = data.finished_at.strftime("%b %d %Y %H:%M:%S")
    #     return data

    @post_dump
    def job_post_dump(self, data, **kwargs):
        status = StatusCode.query.filter_by(id=data["status"]).first()
        user = User.query.filter_by(id=data["user_id"]).first()
        data["status"] = status.message
        data["user"] = user.email
        data.pop("user_id")
        return data

    @pre_load
    def device_db(self, data, **kwargs):
        data["user_id"] = current_user.id
        return data

    @post_load
    def create_devices(self, data, **kwargs):
        if data.get("id"):
            return data
        try:
            # d,_ = Job.get_or_create(db.session, user_id=current_user.id, **data)
            d = Job(**data)
            db.session.add(d)
            db.session.commit()

        except Exception as e:
            raise ValidationException("fail-config", e.error)
        return d
