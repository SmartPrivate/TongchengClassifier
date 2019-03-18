from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_handler import orm_models
from config import settings


def model_setter(src_model: object, des_model: object):
    props = list(filter(lambda o: o[0] != '_', dir(src_model)))
    for prop in props:
        setattr(des_model, prop, getattr(src_model, prop))
    return des_model


class Session(object):
    def __init__(self, connect_str=settings.connect_str):
        engine = create_engine(connect_str)
        self.__session = sessionmaker(
            bind=engine, autoflush=False, expire_on_commit=False)()

    def db_writer(self, model):
        self.__session.add(model)
        self.__session.commit()

    def db_list_writer(self, models):
        self.__session.bulk_save_objects(models)
        self.__session.commit()

    def close_session(self):
        self.__session.close()

    def query_all(self, model_name):
        return self.__session.query(model_name).all()

    def query_image_prediction_by_guid(self, guid):
        return self.__session.query(orm_models.ImagePrediction).filter(orm_models.ImagePrediction.guid == guid).all()
