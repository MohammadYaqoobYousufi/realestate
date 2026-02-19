# Image encoding: from pixel to embedding
# Load and preprocess the image

self.model = resnet50(pretrained=True).to(self.device)
self.preprocess = transform.compose([
  transforms.Resize(image_size),
  transforms.ToTensor(),
  transforms.Normalize(mean=norm_mean, std=norm_std),

])

# ResNet50 feature extraction
features = self.model(input_tensor)
features_vector = features.cpu().numpy().flatten()

# Step 2 similarity search: Finding the fashion match
similarities = cosine_similarity(user_vector.reshape(1, -1),dataset_vectors)
closed_index = np.argmax(similarities)
closed_row = dataset.iloc[closed_index]

# Step 3 Retrieving contextual information
related_items = dataset[dataset["Image URL"] == image_url]

# Step 4 Context-augmented generation using vision-language models
assistant_prompt = (
  f"You're conducting a professional retail catalog analysis."
  f"This image shows standard clothing items available in department stores."
  f"Focus Exclusively on professional fashion analysis for clothing retailer."
  f"ITEM DETAILS (always include this section in your response):\n{items_description}\n\"
  "Please:\n"
  "1. Identify and describe the clothing items objectivity (colors, patterns, materials)\n"
  "2. Categories the overall style (business, casual, etc)\n"
  "3. Include the ITEM DETAILS section at the end\n\n"
  "This is for a professional retail catalog. Use formal, clinical language."
) 

message = [{
  "role": "user",
  "Content": [
    {"type": "text", "text": assistant_prompt}
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + encoded_image}}
  ]
}]

response = self.model.chat(messages=messages)
