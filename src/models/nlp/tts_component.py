import torch
import torchaudio
from transformers import VitsModel, AutoTokenizer

def generate_speech(text):
    print("Loading TTS model...")
    # Load pre-trained model and tokenizer
    model = VitsModel.from_pretrained("facebook/mms-tts-eng")
    tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-eng")

    # Tokenize the text
    inputs = tokenizer(text, return_tensors="pt")

    # Generate speech
    with torch.no_grad():
        output = model(**inputs).waveform 
    
    # Output shape is (1, 1, sequence_length), we need (1, sequence_length) for saving
    return output[0]

if __name__ == "__main__":
    text_input = "Hello! I am running this locally on my laptop without paying for APIs."
    print(f"Generating audio for: '{text_input}'")
    
    audio_data = generate_speech(text_input)
    
    # Save to file
    filepath = "output.wav"
    torchaudio.save(filepath, audio_data, sample_rate=16000)
    print(f"Audio saved to {filepath}")

# End of Version 2

# Start of version 1

# import torch
# import torchaudio
# from transformers import VitsModel, AutoTokenizer

# def generate_speech(text):
#   # load pre-trained model and tokenizer
#   model = VitsModel.from_pretrained("facebook/mms-tts-eng") 
#   tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-eng")

#   # tokeniz the text
#   inputs = tokenizer(text, return_tensors="pt")

#   # Generate speech
#   with torch.no_grad():
#     output = model(**inputs).waveform # No speaker_id
#   return output

# #example usage 
# if __name__ == "__main__":
#   text = "Hello, this is a test of text-to-speech synthesis."
#   audio = generate_speech(text)
#   torchaudio.save("output.wav", audio, sample_rate=16000)