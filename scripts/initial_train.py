#!/usr/bin/env python3
"""
Initial training of TinyGPT model as per spec.
Train model on next-token objective for base competence.
"""

import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import GPT2Config, GPT2LMHeadModel, GPT2Tokenizer
import json
from pathlib import Path

class TextDataset(Dataset):
    def __init__(self, tokenizer, file_paths, max_length=1024):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []

        for file_path in file_paths:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    if 'prompt' in item and 'response' in item:
                        text = item['prompt'] + ' ' + item['response']
                        self.data.append(text)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text = self.data[idx]
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': encoding['input_ids'].flatten()
        }

def train_tinygpt(data_dir="./data/processed", output_dir="./models/tinygpt", epochs=3):
    """Train TinyGPT from scratch"""

    # Model config as per spec
    config = GPT2Config(
        vocab_size=32000,
        n_positions=1024,
        n_embd=512,
        n_layer=6,
        n_head=8,
        n_inner=2048,
        activation_function='gelu_new',
        resid_pdrop=0.1,
        embd_pdrop=0.1,
        attn_pdrop=0.1,
        layer_norm_epsilon=1e-5,
        initializer_range=0.02,
        gradient_checkpointing=False,
        use_cache=True,
        bos_token_id=0,
        eos_token_id=1,
        pad_token_id=2,
    )

    # Initialize model
    model = GPT2LMHeadModel(config)
    print(f"Model parameters: {sum(p.numel() for p in model.parameters())}")

    # Load tokenizer
    tokenizer_path = "./tokenizer"
    if os.path.exists(tokenizer_path):
        tokenizer = GPT2Tokenizer.from_pretrained(tokenizer_path)
        tokenizer.pad_token = tokenizer.eos_token
    else:
        print("Tokenizer not found. Using default GPT2 tokenizer.")
        tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        tokenizer.pad_token = tokenizer.eos_token

    # Prepare data
    data_files = list(Path(data_dir).glob("*.jsonl"))
    if not data_files:
        print("No training data found. Please run preprocess_corpora.py first.")
        return

    dataset = TextDataset(tokenizer, [str(f) for f in data_files])
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4, weight_decay=0.01)

    # Training loop
    model.train()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    for epoch in range(epochs):
        total_loss = 0
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            optimizer.zero_grad()

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs.loss
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

    # Save model
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"Model saved to {output_dir}")

if __name__ == "__main__":
    train_tinygpt()