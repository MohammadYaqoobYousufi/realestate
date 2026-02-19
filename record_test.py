import sounddevice as sd
from scipy.io.wavfile import write

fs = 16000  # Sample rate required by Wav2Vec2
seconds = 5

print("Recording for 5 seconds... Speak now!")
myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
sd.wait()  # Wait until recording is finished
print("Finished recording. Saving as output.wav")
write('output.wav', fs, myrecording)