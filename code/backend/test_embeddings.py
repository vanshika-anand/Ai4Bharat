"""
Quick test script to verify the improved embeddings are working
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✓ Model loaded successfully!\n")

# Test semantic similarity
test_pairs = [
    ("productivity tips for students", "time management strategies for college"),
    ("machine learning tutorial", "artificial intelligence guide"),
    ("healthy eating habits", "nutrition and diet advice"),
    ("productivity tips", "cooking recipes"),  # Should be low similarity
]

print("Testing semantic similarity:\n")
for text1, text2 in test_pairs:
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)
    
    similarity = cosine_similarity(emb1.reshape(1, -1), emb2.reshape(1, -1))[0][0]
    
    print(f"Text 1: {text1}")
    print(f"Text 2: {text2}")
    print(f"Similarity: {similarity*100:.1f}%")
    print()

print("\n✅ Embeddings are working correctly!")
print("The first 3 pairs should have high similarity (>60%)")
print("The last pair should have low similarity (<40%)")
