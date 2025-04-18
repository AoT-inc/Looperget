# coding=utf-8
"""A collection of model factories using factory boy."""
import factory  # factory boy
from looperget.looperget_flask.extensions import db
from looperget.databases import models
from faker import Faker


faker = Faker()


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """A factory for creating user models."""
    class Meta(object):
        model = models.User
        sqlalchemy_session = db.session

    name = faker.name()
    email = faker.email()
