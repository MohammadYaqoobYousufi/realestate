import torch
import librosa
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

def transcribe_audio(audio_path: str):
    print(f"Loading model... please wait.")
    # 1. Load pre-trained model and processor correctly
    processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    model = Wav2Vec2ForCTC.from_pretrained(
        "facebook/wav2vec2-base-960h",
        ignore_mismatched_sizes=True  # Fixed: True must be Capitalized in Python
    )

    # 2. Load and preprocess audio
    # Ensure audio is loaded at 16k sampling rate (required by Wav2Vec2)
    audio, sr = librosa.load(audio_path, sr=16000)
    
    # Process audio into tensors
    inputs = processor(audio, sampling_rate=sr, return_tensors="pt")

    # 3. Generate transcription
    with torch.no_grad():
        # Fixed: variable name was 'logit' but used 'logits' later
        logits = model(inputs.input_values).logits
        
        # Decode the logits to text
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids)
        
        return transcription[0]

# Example usage
if __name__ == "__main__":
    # Make sure you have a file named 'output.wav' in the same folder, 
    # or change this to an existing file path.
    try:
        text = transcribe_audio("output.wav")
        print(f"Transcription: {text}")
    except FileNotFoundError:
        print("Error: 'output.wav' not found. Please provide a valid audio file.")


# import torch
# import librosa
# from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
# from typing import Union, List


# def transcribe_audio(audio_path: str):
#   #load pre-trained model and processor
#   processor = Wav2Vec2Processor.from.pretrained("facebook/wav2vec2-base-960h")
#   model = Wav2Vec2ForCTC.from.pretrained("facebook/wav2vec2-base-960h",ignore_mismatched_sizes=true
#   # add this parameter
#   )
#   # Load and preprocess audio
#   audio, sr = librosa.load(audio_path, sr=16000)
#   inputs = processor(audio, sampling_rate=sr, return_tensors="pt")

#   # Generate transcription
#   with torch.no_grad():
#     logit = model(inputs.input_values).logits
#     # decode the logits to text
#     predicted_ids =  torch.argmax(logits, dim=-1)
#     transcription = processor.batch_decode(predicted_ids)
#     return transcription[0]

# # Example usage 

# text = transcribe_audio("output.wav")
# print(f"transcription:{text}") 
