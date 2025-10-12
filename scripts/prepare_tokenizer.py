#!/usr/bin/env python3
"""
Prepare tokenizer for TinyGPT training as per spec.
Trains a 32k BPE tokenizer from scratch.
"""

import os
import json
from pathlib import Path
from tokenizers import ByteLevelBPETokenizer

def prepare_tokenizer(corpus_path, vocab_size=32000, output_dir="./tokenizer"):
    """Train BPE tokenizer from corpus"""
    print(f"Training BPE tokenizer with vocab_size={vocab_size}")

    # Initialize tokenizer
    tokenizer = ByteLevelBPETokenizer()

    # Train on corpus
    tokenizer.train(
        files=[corpus_path],
        vocab_size=vocab_size,
        min_frequency=2,
        special_tokens=["<pad>", "<unk>", "<s>", "</s>"]
    )

    # Save tokenizer
    os.makedirs(output_dir, exist_ok=True)
    tokenizer.save_model(output_dir)

    print(f"Tokenizer saved to {output_dir}")
    return tokenizer

if __name__ == "__main__":
    # Example usage
    corpus_path = "data/training_corpus.txt"  # Should be prepared separately
    if os.path.exists(corpus_path):
        prepare_tokenizer(corpus_path)
    else:
        print(f"Corpus file {corpus_path} not found. Please prepare training data first.")