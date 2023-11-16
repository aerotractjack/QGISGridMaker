from flask import Flask, request, jsonify
from flasgger import swag_from, Swagger
from flask_executor import Executor
from gridmaker import GridMaker, log

app = Flask(__name__)
swagger = Swagger(app)
executor = Executor(app)

template = {
    "swagger": "2.0",
    "info": {
        "title": "GridMaker API Documentation",
        "description": "API documentation for the Aerotract GridMaker service",
        "version": "1.0.0"
    }
}

swag = swag_from({
    'responses': {
        200: {
            'description': 'Success',
            'schema': {
                'type': 'string',
                'example': 'Generation submitted successfully.'
            }
        },
        500: {
            'description': 'Failure',
            'schema': {
                'type': 'string',
                'example': '<insert error message here>'
            }
        },
    },
    'parameters': [{
        'name': 'entry',
        'description': 'Client/Project/Stand IDs in dictionary format',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'CLIENT_ID': {
                    'type': 'string',
                    'description': 'Client ID',
                    'example': '10007'
                },
                'PROJECT_ID': {
                    'type': 'string',
                    'description': 'Project ID',
                    'example': '101036'
                },
                'STAND_ID': {
                    'type': 'string',
                    'description': 'Stand ID',
                    'example': '103'
                }
            },
            'required': ['CLIENT_ID', 'PROJECT_ID', 'STAND_ID']
        }
    }]
})

@app.route("/", methods=["GET", "POST"])
@swag
def submit():
    """
    Submit a stand to have a plot grid generated
    """
    contents = request.get_json()
    contents = {k.lower(): v for k,v in contents.items()}
    try:
        executor.submit(GridMaker.FromIDs, **contents)
        return jsonify("submitted aoi generated")
    except Exception as e:
        log(e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=7115, debug=True, host="0.0.0.0")
