from io import BytesIO
import re
import wave

from .models import Account, Role
from .storage import Store

RATE = 16_000
SECONDS = 3
PHRASE = "The bookstore is open and I would like to find a book."


def record_sample() -> bytes:
    try:
        import sounddevice
    except ImportError as error:
        raise ValueError("Install the voice dependencies with python -m pip install -r requirements.txt.") from error
    try:
        recording = sounddevice.rec(RATE * SECONDS, samplerate=RATE, channels=1, dtype="int16")
        sounddevice.wait()
    except sounddevice.PortAudioError as error:
        raise ValueError("The default microphone is unavailable.") from error
    buffer = BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        output.writeframes(recording.astype("<i2").tobytes())
    return buffer.getvalue()


def voice_features(sample: bytes) -> list[float]:
    try:
        import numpy as np
    except ImportError as error:
        raise ValueError("Install the voice dependencies with python -m pip install -r requirements.txt.") from error
    try:
        with wave.open(BytesIO(sample), "rb") as source:
            if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, RATE):
                raise ValueError("Use a mono 16-bit PCM recording at 16 kHz.")
            signal = np.frombuffer(source.readframes(RATE * 10), dtype="<i2").astype(float) / 32768
    except (EOFError, wave.Error) as error:
        raise ValueError("The voice sample is unreadable.") from error

    frame_size = 400
    if len(signal) < RATE or np.max(np.abs(signal)) < 0.01:
        raise ValueError("The sample is too short or quiet. Please speak clearly.")
    frames = np.lib.stride_tricks.sliding_window_view(signal, frame_size)[::160]
    energy = np.sqrt(np.mean(frames ** 2, axis=1))
    frames = frames[energy >= max(0.004, 0.12 * energy.max())]
    if len(frames) < 25:
        raise ValueError("The sample did not contain enough audible speech.")
    spectra = abs(np.fft.rfft(frames * np.hanning(frame_size), n=512)) ** 2
    bins = np.unique(np.round(np.geomspace(4, 240, 21)).astype(int))
    band_energy = np.column_stack(
        [spectra[:, start:end].mean(axis=1) for start, end in zip(bins, bins[1:])]
    )
    bands = np.log(band_energy + 1e-8)
    bands -= bands.mean(axis=1, keepdims=True)
    feature = np.concatenate((np.median(bands, axis=0), np.std(bands, axis=0)))
    norm = np.linalg.norm(feature)
    if norm == 0:
        raise ValueError("The sample did not contain usable voice features.")
    return (feature / norm).tolist()


class VoiceClassifier:
    """A local nearest-neighbor classifier for the course prototype."""

    def __init__(self, store: Store):
        self.store = store

    def identify(self, modality: str, sample: bytes) -> str | None:
        if modality != "voice":
            return None
        features = voice_features(sample)
        scores = [
            (max(sum(left * right for left, right in zip(features, profile))
                 for profile in profiles), account_id)
            for account_id, profiles in self.store.voice_profiles.items() if profiles
        ]
        scores.sort(reverse=True)
        if not scores or scores[0][0] < 0.88:
            return None
        if len(scores) > 1 and scores[0][0] - scores[1][0] < 0.025:
            return None
        return scores[0][1]

    def enroll(self, username: str, samples: list[bytes], role: Role = Role.CUSTOMER) -> Account:
        account_id = username.strip().casefold()
        if not re.fullmatch(r"[a-z0-9_]{3,24}", account_id):
            raise ValueError("Use 3 to 24 letters, digits, or underscores for the username.")
        if account_id in self.store.accounts:
            raise ValueError("That username already exists.")
        if len(samples) != 3:
            raise ValueError("Enrollment requires three voice samples.")
        profiles = [voice_features(sample) for sample in samples]
        account = Account(account_id, role)
        with self.store.change_activity():
            self.store.accounts[account_id] = account
            self.store.voice_profiles[account_id] = profiles
        return account
