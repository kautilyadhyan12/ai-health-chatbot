"""
Embedding generation for medical text using sentence-transformers/all-mpnet-base-v2
"""
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import warnings
warnings.filterwarnings('ignore')

class EmbeddingGenerator:
    """Generate embeddings for medical text"""
    
    def __init__(self, model_name='sentence-transformers/all-mpnet-base-v2'):
        """
        Initialize embedding generator
        
        Args:
            model_name (str): Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            print(f"✅ Embedding model loaded successfully on {self.device}")
            print(f"Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            print(f"❌ Error loading model {self.model_name}: {e}")
            
            try:
                self.model_name = 'all-MiniLM-L6-v2'
                self.model = SentenceTransformer(self.model_name, device=self.device)
                print(f"✅ Loaded fallback model: {self.model_name}")
            except Exception as e2:
                print(f"❌ Failed to load fallback model: {e2}")
                raise
    
    def get_embeddings(self, texts, batch_size=32, show_progress_bar=False):
        """
        Generate embeddings for a list of texts
        
        Args:
            texts (list): List of text strings
            batch_size (int): Batch size for processing
            
        Returns:
            numpy.ndarray: Array of embeddings
        """
        if not texts:
            return np.array([])
        
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            # Convert texts to embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True,
                normalize_embeddings=True,
                device=self.device
            )
            
            return embeddings
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            # Return zero embeddings as fallback
            embedding_dim = self.model.get_sentence_embedding_dimension()
            return np.zeros((len(texts), embedding_dim))
    
    def get_single_embedding(self, text):
        """
        Generate embedding for a single text
        
        Args:
            text (str): Input text
            
        Returns:
            numpy.ndarray: Single embedding vector
        """
        return self.get_embeddings([text])[0]
    
    def get_similarity(self, text1, text2):
        """
        Calculate cosine similarity between two texts
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Cosine similarity score (0-1)
        """
        emb1 = self.get_single_embedding(text1)
        emb2 = self.get_single_embedding(text2)
        
        # Calculate cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return float(similarity)
    
    def find_most_similar(self, query, candidates, top_k=3, threshold=0.5):
        """
        Find most similar candidates to query
        
        Args:
            query (str): Query text
            candidates (list): List of candidate texts
            top_k (int): Number of top results to return
            threshold (float): Similarity threshold
            
        Returns:
            list: List of (index, similarity_score, text) tuples
        """
        if not candidates:
            return []
        
        query_embedding = self.get_single_embedding(query)
        candidate_embeddings = self.get_embeddings(candidates)
        
        # Calculate similarities
        similarities = []
        for i, cand_emb in enumerate(candidate_embeddings):
            similarity = np.dot(query_embedding, cand_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(cand_emb)
            )
            if similarity >= threshold:
                similarities.append((i, float(similarity), candidates[i]))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_embedding_dimension(self):
        """Get the dimension of embeddings"""
        return self.model.get_sentence_embedding_dimension()
    
    def save_embeddings(self, texts, output_path):
        """
        Save embeddings to file
        
        Args:
            texts (list): List of texts
            output_path (str): Path to save embeddings
        """
        embeddings = self.get_embeddings(texts)
        np.save(output_path, embeddings)
        print(f"✅ Saved embeddings to {output_path}")
    
    def load_embeddings(self, input_path):
        """
        Load embeddings from file
        
        Args:
            input_path (str): Path to embeddings file
            
        Returns:
            numpy.ndarray: Loaded embeddings
        """
        return np.load(input_path)