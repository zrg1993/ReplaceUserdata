from unittest import TestCase
import json

# from flask_restful_graph import *
# from flask_restful_graph.models import app, graph_connection
from flask_restful_graph.models import Group, User
import os

from flask import Flask
from flask_restful import Api
from py2neo import Graph

from models import BaseModel, Group, User
from resource_factory import ResourceFactory


app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

app.config.from_envvar('RESTFUL_GRAPH_SETTINGS', silent=True)


def init_db(password):
    return Graph(password=password)


# graph_password = os.environ.get('TEST_GRAPH_PASSWORD')
graph_connection = init_db("iwate")
resource_factory = ResourceFactory(graph=graph_connection)


group_resource, groups_resource = \
    resource_factory.get_individual_and_collection_resources(Group)
user_resource, users_resource = \
    resource_factory.get_individual_and_collection_resources(User)
relationship_resources = \
    resource_factory.get_relationship_resources(BaseModel.related_models)

api.add_resource(groups_resource, '/groups/')
api.add_resource(group_resource, '/groups/<int:id>')
api.add_resource(users_resource, '/users/')
api.add_resource(user_resource, '/users/<int:id>')

for resource, url in relationship_resources:
    api.add_resource(resource, url)


HOST = 'http://localhost'

def get_by_id(cls, id):
    return cls.select(graph_connection, id).first()


class TestSerializingNodes(TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_requesting_relationships_1(self):
        rv = self.app.get('/users/8/relationships/groups')
        data = json.loads(rv.data)

        self.assertEqual(len(data), 2)
        self.assertEqual(data['data'][0]['type'], 'group')
        self.assertEqual(data['data'][0]['id'], '11')
        self.assertEqual(
            data['links']['self'],
            HOST + '/users/8/relationships/groups'
        )

    def test_getting_models_relationships_1(self):
        user = get_by_id(User, 8)

        included, relationships = user.get_relationships()

        self.assertEqual(included, [{
            'attributes': {
                'title': 'This is a group',
            },
            'type': 'group',
            'id': '11'
        }])

        self.assertEqual(relationships, {
            'groups': {
                'data': [
                    {
                        'type': 'group',
                        'id': '11'
                    }
                ],
                'links': {}
            }
        })

    def test_getting_models_relationships_2(self):
        group = get_by_id(Group, 11)

        included, relationships = group.get_relationships()

        self.assertEqual(included, [{
            'attributes': {
                'email': 'guy@place.com',
                'firstName': 'Guy'
            },
            'type': 'user',
            'id': '9'
        }, {
            'attributes': {
                'email': 'new4@place.com',
                'firstName': 'Guy'
            },
            'type': 'user',
            'id': '8'
            }])

        self.assertEqual(relationships, {
            'members': {
                'data': [
                    {
                        'type': 'user',
                        'id': '9'
                    }, {
                        'type': 'user',
                        'id': '8'
                    }
                ],
                'links': {}
            }
        })
