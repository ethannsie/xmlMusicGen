import argparse
from pydub import AudioSegment
import pydub.scipy_effects
import numpy as np
import scipy
import matplotlib.pyplot as plt
import fluidsynth
import time

from utils import (
    frequency_spectrum,
    calculate_distance,
    classify_note_attempt_1,
    classify_note_attempt_2,
    classify_note_attempt_3,
)


def predict_note_starts(song, plot, actual_starts):
    SEGMENT_MS = 50
    VOLUME_THRESHOLD = -35
    EDGE_THRESHOLD = 5
    MIN_MS_BETWEEN = 100

    song = song.high_pass_filter(80, order=4)
    volume = [segment.dBFS for segment in song[::SEGMENT_MS]]

    predicted_starts = []
    for i in range(1, len(volume)):
        if volume[i] > VOLUME_THRESHOLD and volume[i] - volume[i - 1] > EDGE_THRESHOLD:
            ms = i * SEGMENT_MS
            if len(predicted_starts) == 0 or ms - predicted_starts[-1] >= MIN_MS_BETWEEN:
                predicted_starts.append(ms)

    if len(actual_starts) > 0:
        print("Approximate actual note start times ({})".format(len(actual_starts)))
        print(" ".join(["{:5.2f}".format(s) for s in actual_starts]))
        print("Predicted note start times ({})".format(len(predicted_starts)))
        print(" ".join(["{:5.2f}".format(ms / 1000) for ms in predicted_starts]))

    if plot:
        x_axis = np.arange(len(volume)) * (SEGMENT_MS / 1000)
        plt.plot(x_axis, volume)

        for s in actual_starts:
            plt.axvline(x=s, color="r", linewidth=0.5, linestyle="-")
        for ms in predicted_starts:
            plt.axvline(x=(ms / 1000), color="g", linewidth=0.5, linestyle=":")

        plt.show()

    return predicted_starts


import math

# Function to identify the octave of a frequency
def identify_octave(frequency):
    """
    Identify the octave of a note based on its frequency.

    Args:
        frequency (float): The frequency of the note in Hz.

    Returns:
        int: The octave number.
    """
    # Reference frequency for A4 (440 Hz)
    A4_FREQUENCY = 440.0

    # Calculate the number of octaves above or below A4
    semitones_from_A4 = 12 * math.log2(frequency / A4_FREQUENCY)
    octave = 4 + (semitones_from_A4 // 12)

    return int(octave)


def predict_notes(song, starts, actual_notes, plot_fft_indices):
    predicted_notes = []
    for i, start in enumerate(starts):
        sample_from = start + 50
        sample_to = start + 550
        if i < len(starts) - 1:
            sample_to = min(starts[i + 1], sample_to)
        segment = song[sample_from:sample_to]
        freqs, freq_magnitudes = frequency_spectrum(segment)

        # Predict the note and calculate the octave
        predicted_note = classify_note_attempt_3(freqs, freq_magnitudes)
        if predicted_note:
            # Extract the peak frequency to determine the octave
            peak_index = np.argmax(freq_magnitudes)
            peak_frequency = freqs[peak_index]
            octave = identify_octave(peak_frequency)

            # Combine the note and octave
            predicted_note_with_octave = f"{predicted_note}{octave}"
            predicted_notes.append(predicted_note_with_octave)
        else:
            predicted_notes.append("U")  # Append "U" for unknown

        print("")
        print("Note: {}".format(i))
        if i < len(actual_notes):
            print("Predicted: {} Actual: {}".format(predicted_note_with_octave, actual_notes[i]))
        else:
            print("Predicted: {}".format(predicted_note_with_octave))
        print("Predicted start: {}".format(start))
        length = sample_to - sample_from
        print("Sampled from {} to {} ({} ms)".format(sample_from, sample_to, length))
        print("Frequency sample period: {}hz".format(freqs[1]))

        peak_indicies, props = scipy.signal.find_peaks(freq_magnitudes, height=0.015)
        print("Peaks of more than 1.5 percent of total frequency contribution:")
        for j, peak in enumerate(peak_indicies):
            freq = freqs[peak]
            magnitude = props["peak_heights"][j]
            print("{:.1f}hz with magnitude {:.3f}".format(freq, magnitude))

        if i in plot_fft_indices:
            plt.plot(freqs, freq_magnitudes, "b")
            plt.xlabel("Freq (Hz)")
            plt.ylabel("|X(freq)|")
            plt.show()
    return predicted_notes


def process_file(file, note_file=None, note_starts_file=None, plot_starts=False, plot_fft_indices=[]):
    actual_starts = []
    if note_starts_file:
        with open(note_starts_file) as f:
            for line in f:
                actual_starts.append(float(line.strip()))

    actual_notes = []
    if note_file:
        with open(note_file) as f:
            for line in f:
                actual_notes.append(line.strip())

    song = AudioSegment.from_file(file)
    song = song.high_pass_filter(80, order=4)

    starts = predict_note_starts(song, plot_starts, actual_starts)

    predicted_notes = predict_notes(song, starts, actual_notes, plot_fft_indices)

    if actual_notes:
        lev_distance = calculate_distance(predicted_notes, actual_notes)
        print("Levenshtein distance: {}/{}".format(lev_distance, len(actual_notes)))

    return predicted_notes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--note-file", type=str)
    parser.add_argument("--note-starts-file", type=str)
    parser.add_argument("--plot-starts", action="store_true")
    parser.add_argument(
        "--plot-fft-index",
        type=int,
        nargs="*",
        help="Index of detected note to plot graph of FFT for",
    )
    args = parser.parse_args()
    predicted_notes = process_file(
        args.file,
        note_file=args.note_file,
        note_starts_file=args.note_starts_file,
        plot_starts=args.plot_starts,
        plot_fft_indices=(args.plot_fft_index or []),
    )

    note_sequences = []
    for note in predicted_notes:
        note_sequences.append([note])

    def note_to_midi(note):
        if note in ["00", "0", "", None]:
            return None
        try:
            note_map = ['C', 'C#', 'D', 'D#', 'E', 'F',
                        'F#', 'G', 'G#', 'A', 'A#', 'B']
            if len(note) == 2:
                key, octave = note[0], int(note[1])
            elif len(note) == 3:
                key, octave = note[:2], int(note[2])
            else:
                return None
            return note_map.index(key) + 12 * (octave + 1)
        except:
            return None

    SOUNDFONT_PATH = "FluidR3_GM/FluidR3_GM.sf2"
    fs = fluidsynth.Synth()
    fs.start()
    sfid = fs.sfload(SOUNDFONT_PATH)
    fs.program_select(0, sfid, 0, 0)

    def play_chords(chords, duration=0.1, velocity=100):
        current = set()
        for chord in chords:
            print("Now playing:", chord)
            next_notes = set(filter(None, (note_to_midi(n) for n in chord)))
            for note in current - next_notes:
                fs.noteoff(0, note)
            for note in next_notes - current:
                fs.noteon(0, note, velocity)
            time.sleep(duration)
            current = next_notes
        for note in current:
            fs.noteoff(0, note)

    play_chords(note_sequences, duration=0.3)
    fs.delete()
