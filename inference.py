"""Standalone CPU inference without importing the training or web stack."""
import argparse
import json
from pathlib import Path

import torch

from lstm_audio import LSTMAudio
from preprocess_midi_inference_data import PreprocessMIDIInferenceData


ROOT = Path(__file__).resolve().parent


def load_inference_model(model_path, config_path=None):
    config_path = Path(config_path) if config_path else ROOT/'example/trains.example.json'
    with config_path.open(encoding='utf-8') as file:
        configurations = json.load(file)
    if not isinstance(configurations, list) or len(configurations) != 1:
        raise ValueError('Inference configuration must contain exactly one model parameter set')
    config = configurations[0]
    model = LSTMAudio(**config['lstm_model_params'], model_layers=config['model_layers'])
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'], strict=True)
    return model.eval()


def inference(model_path, input_midi_file, output_midi_file, config_path=None):
    if input_midi_file is output_midi_file or (
        not hasattr(input_midi_file, 'read') and not hasattr(output_midi_file, 'write')
        and Path(input_midi_file).resolve() == Path(output_midi_file).resolve()
    ):
        raise ValueError('Choose a different output file to preserve the original MIDI')
    model = load_inference_model(model_path, config_path)
    with torch.inference_mode():
        midi = PreprocessMIDIInferenceData.get_left_right_hands_midifile(model, input_midi_file)
    if hasattr(output_midi_file, 'write'):
        midi.save(file=output_midi_file)
    else:
        midi.save(filename=output_midi_file)


def main():
    parser = argparse.ArgumentParser(description='Predict piano hands while preserving source MIDI events.')
    parser.add_argument('model_path', help='Path to the original model checkpoint.')
    parser.add_argument('input_midi_file', help='Input MIDI file.')
    parser.add_argument('output_midi_file', help='Output MIDI file (different from input).')
    parser.add_argument('--config', help='JSON file containing one matching model parameter set.')
    args = parser.parse_args()
    try:
        inference(args.model_path, args.input_midi_file, args.output_midi_file, args.config)
    except (OSError, ValueError, RuntimeError, KeyError, EOFError) as error:
        parser.exit(2, f'Error: {error}\n')


if __name__ == '__main__':
    main()
