#!/usr/bin/env python3
"""
Preprocess corpora for TinyGPT training as per spec.
Generate .jsonl shards with prompts/responses + metadata.
"""

import os
import json
import random
from pathlib import Path

def preprocess_instruction_data(input_files, output_dir="./data/processed"):
    """Process instruction tuning datasets"""
    os.makedirs(output_dir, exist_ok=True)

    processed_data = []

    for input_file in input_files:
        if not os.path.exists(input_file):
            continue

        print(f"Processing {input_file}")

        with open(input_file, 'r', encoding='utf-8') as f:
            if input_file.endswith('.json'):
                data = json.load(f)
            elif input_file.endswith('.jsonl'):
                data = [json.loads(line) for line in f]

        for item in data:
            # Format as instruction-response pairs
            if 'instruction' in item and 'output' in item:
                prompt = f"Instruction: {item['instruction']}\nResponse:"
                response = item['output']

                processed_data.append({
                    'prompt': prompt,
                    'response': response,
                    'type': 'instruction',
                    'source': os.path.basename(input_file)
                })

    # Save as jsonl shards
    shard_size = 10000
    for i in range(0, len(processed_data), shard_size):
        shard = processed_data[i:i+shard_size]
        shard_file = os.path.join(output_dir, f"instruction_shard_{i//shard_size}.jsonl")

        with open(shard_file, 'w', encoding='utf-8') as f:
            for item in shard:
                f.write(json.dumps(item) + '\n')

    print(f"Processed {len(processed_data)} instruction pairs into {len(processed_data)//shard_size + 1} shards")

def preprocess_conversation_data(input_files, output_dir="./data/processed"):
    """Process conversational datasets"""
    os.makedirs(output_dir, exist_ok=True)

    processed_data = []

    for input_file in input_files:
        if not os.path.exists(input_file):
            continue

        print(f"Processing {input_file}")

        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Simple conversation parsing (assuming alternating user/assistant)
        conversation = []
        for line in lines:
            line = line.strip()
            if line.startswith('User:'):
                if conversation:
                    processed_data.append({
                        'conversation': conversation,
                        'type': 'conversation',
                        'source': os.path.basename(input_file)
                    })
                    conversation = []
                conversation.append({'role': 'user', 'content': line[5:].strip()})
            elif line.startswith('Assistant:') or line.startswith('AI:'):
                conversation.append({'role': 'assistant', 'content': line[10:].strip()})

        if conversation:
            processed_data.append({
                'conversation': conversation,
                'type': 'conversation',
                'source': os.path.basename(input_file)
            })

    # Save as jsonl shards
    shard_size = 5000
    for i in range(0, len(processed_data), shard_size):
        shard = processed_data[i:i+shard_size]
        shard_file = os.path.join(output_dir, f"conversation_shard_{i//shard_size}.jsonl")

        with open(shard_file, 'w', encoding='utf-8') as f:
            for item in shard:
                f.write(json.dumps(item) + '\n')

    print(f"Processed {len(processed_data)} conversations into {len(processed_data)//shard_size + 1} shards")

if __name__ == "__main__":
    # Example usage - adjust paths as needed
    instruction_files = ["data/instruction_dataset.json", "data/code_instructions.jsonl"]
    conversation_files = ["data/conversation_corpus.txt", "data/dialogue_data.txt"]

    preprocess_instruction_data(instruction_files)
    preprocess_conversation_data(conversation_files)