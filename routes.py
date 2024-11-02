from flask_restful import Api
from presentations.example import Example
def routes(app):

    api = Api(app)
    api.prefix = '/v1'
    api.add_resource(Example, '/examples/<example_id>', endpoint='example_get')