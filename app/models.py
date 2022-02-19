from marshmallow_sqlalchemy import SQLAlchemySchema
from app import db
from sqlalchemy.sql import ClauseElement


class Base(db.Model):

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    date_modified = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)


    @classmethod
    def get_or_create(cls, session, defaults=None, **kwargs):
        instance = session.query(cls).filter_by(**kwargs).one_or_none()
        if instance:
            return instance, False
        else:
            params = {k: v for k, v in kwargs.items() if not isinstance(v, ClauseElement)}
            params.update(defaults or {})
            instance = cls(**params)
            try:
                session.add(instance)
                session.commit()
            except Exception: 
                # The actual exception depends on the specific database so we catch all exceptions. 
                # This is similar to the official 
                # documentation: https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html
                session.rollback()
                instance = session.query(cls).filter_by(**kwargs).one()
                return instance, False
            else:
                return instance, True

class BaseSchema(SQLAlchemySchema):
    class Meta:
        pass
