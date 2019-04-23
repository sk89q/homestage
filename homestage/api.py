from flask import Flask, request, jsonify

from homestage.model import MediaSchema, StartDateTimeSchema


class WebServer:
    def __init__(self, stage, host, port):
        self.stage = stage
        self.host = host
        self.port = port

    def start(self):
        app = Flask(__name__)

        @app.route('/api/media/', methods=['POST'])
        def new_song():
            data = request.get_json()
            result = MediaSchema().load(data)
            if len(result.errors):
                return jsonify({'errors': result.errors}, 401)
            else:
                self.stage.state.reset(result.data)
                return jsonify({"success": True})

        @app.route('/api/media/position/', methods=['POST'])
        def position():
            data = request.get_json()
            result = StartDateTimeSchema().load(data)
            if len(result.errors):
                return jsonify({'errors': result.errors}, 401)
            else:
                self.stage.state.media.start_datetime = result.data
                return jsonify({"success": True})

        @app.route('/api/enabled/', methods=['POST'])
        def update_status():
            data = request.get_json()
            if data.get('enabled', False):
                self.stage.enabled = True
            else:
                self.stage.enabled = False
            return jsonify({"success": True})

        app.run(debug=False, host=self.host, port=self.port, threaded=False)
