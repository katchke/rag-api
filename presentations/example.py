from flask_restful import Resource
from flask import jsonify, make_response
from applications.example import ExampleService
from domains.errors import NotFoundException, BadRequestException

 
class Example(Resource):
    def get(self, example_id):
        print("Example get() ====>")

        try:
            example = ExampleService().get_example_by_id(example_id)
    
            print("Example() get completed====>")
            return make_response(jsonify(example), 200)
    
        except NotFoundException as ex:
            print(f"NotFoundException Error Example post() {str(ex)}")
            return make_response(jsonify({"message": str(ex)}), 404)
        
        except BadRequestException as ex:
            print(f"BadRequestException Error Example post() {str(ex)}")
            return make_response(jsonify({"message": str(ex)}), 400)

        except Exception as ex:
            print(f"Exception Error Example post() {str(ex)}")
            return make_response(jsonify(
                {"message": str(ex)}
            ), 500)
