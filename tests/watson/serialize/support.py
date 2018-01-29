# -*- coding: utf-8 -*-
import enum
import sqlalchemy
from sqlalchemy.ext import declarative
from sqlalchemy import orm, Column, Integer
from watson.db import repositories, utils
from watson.routing import routers
from watson.serialize.decorators import serialize
from watson.serialize import errors


BaseModel = declarative.declarative_base()


class ModelEnum(enum.Enum):
    test = 'testing'


class Model(BaseModel):

    __tablename__ = 'models'

    class Meta(object):
        attributes = (
            'id',
            'name',
            'instances',
            'instance',
            'enum_value'
        )
        strategies = {
            'enum_value': lambda x: x.name if x else ''
        }
        route = 'models'

    id = Column(Integer, primary_key=True)
    name = None
    instances = None
    instance = None
    enum_value = None
    protected_value = 'protected'


class SubModel(BaseModel):

    __tablename__ = 'sub_models'

    class Meta(object):
        attributes = (
            'id',
            'value'
        )
        route = 'submodels'

    id = Column(Integer, primary_key=True)
    value = None


class Repository(repositories.Base):
    __model__ = Model


def generate_model(**kwargs):
    model = Model(**kwargs)
    model.enum_value = ModelEnum.test
    return model


def sample_repository():
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    session = orm.sessionmaker(bind=engine)()
    BaseModel.metadata.create_all(engine)
    model = generate_model()
    session.add(model)
    session.commit()
    return Repository(session)


def sample_router():
    return routers.Dict({
        'models': {
            'path': '/models[/:id]'
        },
        'submodels': {
            'path': '/submodels[/:id]'
        }
    })


class RestError(errors.Base):
    pass


class Controller(object):
    @serialize(router=sample_router())
    def action(self):
        return generate_model(id=1, name='Test')

    @serialize(router=sample_router())
    def pagination_action(self):
        repository = sample_repository()
        paginator = utils.Pagination(repository.query)
        return paginator

    @serialize(router=sample_router())
    def nested_object_action(self):
        model = Model(id=1, name='Model1', enum_value=ModelEnum.test)
        model.instance = SubModel(id=2, value='SubModel')
        model2 = Model(id=3, name='Model2', instance=model)
        model.instances = [
            model2
        ]
        return model

    @serialize(router=sample_router())
    def error_action(self):
        raise RestError(code='10')
