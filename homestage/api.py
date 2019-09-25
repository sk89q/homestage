from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

from homestage.controller import HomeStage
from homestage.model import MediaSchema, StartDateTimeSchema


class WebServer:
    def __init__(self, stage: HomeStage):
        self.stage = stage

    def start(self):
        config = self.stage.config

        app = Flask(__name__)
        app.config['SECRET_KEY'] = config.http_secret_key
        socketio = SocketIO(app)

        def send_config():
            emit('status', {
                'microphones': [{
                    'value': mic.id,
                    'label': mic.name,
                } for mic in config.get_microphones()],
                'microphone': {
                    'value': config.microphone.id,
                    'label': config.microphone.name,
                } if config.microphone else None,
            })

        def send_status():
            emit('status', {
                'enabled': self.stage.enabled,
                'beat': bool(self.stage.state.beat),
                'currentTempo': self.stage.state.current_tempo,
                'spectrumAdjusted': list(self.stage.state.spectrum_adjusted),
                'media': {
                    'artist': self.stage.state.media.artist,
                    'title': self.stage.state.media.title,
                    'uri': self.stage.state.media.uri,
                    'type': self.stage.state.media.type,
                    'position': self.stage.state.media.position,
                }
            })

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

        @app.route('/')
        def control():
            return render_template('ui.html')

        @socketio.on('initialize')
        def initialize(message):
            send_config()
            send_status()

        @socketio.on('setmicrophone')
        def set_microphone(message):
            config.microphone = str(message['value']) if message is not None else None
            config.save()
            send_config()

        @socketio.on('setcontrol')
        def set_control(message):
            self.stage.control.axis0 = [float(message['axis0'][0]), float(message['axis0'][1])]
            self.stage.control.axis1 = [float(message['axis1'][0]), float(message['axis1'][1])]
            for key in ('lb', 'rb', 'left', 'right', 'up', 'down', 'triangle', 'square', 'circle', 'cross'):
                setattr(self.stage.control, key, bool(message[key]))
            for key in ('lt', 'rt'):
                setattr(self.stage.control, key, float(message[key]))
            send_status()

        @socketio.on('poll')
        def poll(message):
            send_status()

        socketio.run(app, debug=config.debug, host=config.http_bind_address, port=config.http_port)
