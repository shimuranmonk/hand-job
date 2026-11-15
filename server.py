"""Local Flask preview for hand suggestions, manual corrections, and validated MIDI."""
import json
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, render_template, request, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from hand_service import InvalidMIDIInput, analyze_midi, corrected_export
from inference import load_inference_model
from midi_validation import MIDIIntegrityError

ROOT = Path(__file__).resolve().parent


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        MAX_MIDI_NOTES=20000,
        MODEL_PATH=ROOT/'example/checkpoint.pth',
        MODEL_LOADER=load_inference_model,
        SEND_FILE_MAX_AGE_DEFAULT=0,
    )
    if config:
        app.config.update(config)
    limiter = Limiter(key_func=get_remote_address, app=app, storage_uri='memory://',
                      default_limits=['200 per day', '50 per hour'])
    app.extensions['handjob_limiter'] = limiter
    model_lock = Lock()

    def model():
        with model_lock:
            if 'handjob_model' not in app.extensions:
                app.extensions['handjob_model'] = app.config['MODEL_LOADER'](app.config['MODEL_PATH'])
            return app.extensions['handjob_model']

    def uploaded_data():
        if 'midi' not in request.files:
            raise InvalidMIDIInput('Choose a MIDI file first.')
        return request.files['midi'].read()

    def download(output):
        return send_file(output, mimetype='audio/midi', as_attachment=True,
                         download_name='handjob.mid', max_age=0)

    @app.after_request
    def no_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(InvalidMIDIInput)
    def bad_input(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(MIDIIntegrityError)
    def unsafe_export(error):
        return jsonify(error='This MIDI cannot be split safely: ' + str(error)), 422

    @app.errorhandler(413)
    def too_large(error):
        return jsonify(error='The file is too large. Choose a MIDI smaller than 16 MB.'), 413

    @app.errorhandler(429)
    def too_many(error):
        return jsonify(error='Please wait before processing another file.'), 429

    @app.errorhandler(500)
    def server_error(error):
        return jsonify(error='The file could not be processed. See the local server log for details.'), 500

    @app.get('/')
    def home():
        return render_template('index.html')

    @app.post('/api/analyze')
    @limiter.limit('2 per minute')
    def analyze():
        data = uploaded_data()
        # Validate before loading the checkpoint on the first request.
        from hand_service import parse_source
        parse_source(data, app.config['MAX_MIDI_NOTES'])
        return jsonify(analyze_midi(data, model(), app.config['MAX_MIDI_NOTES']))

    @app.post('/api/export')
    @limiter.limit('30 per minute')
    def export():
        data = uploaded_data()
        try:
            assignments = json.loads(request.form.get('assignments', ''))
        except (TypeError, ValueError) as error:
            raise InvalidMIDIInput('Hand choices could not be read. Import the MIDI again.') from error
        return download(corrected_export(data, assignments, app.config['MAX_MIDI_NOTES']))

    @app.post('/midi-to-midi')
    @limiter.limit('2 per minute')
    def convert():
        data = request.get_data()
        from hand_service import parse_source
        parse_source(data, app.config['MAX_MIDI_NOTES'])
        result = analyze_midi(data, model(), app.config['MAX_MIDI_NOTES'])
        choices = {note['id']: note['hand'] for note in result['notes']}
        return download(corrected_export(data, choices, app.config['MAX_MIDI_NOTES']))

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
