# embeddings/embedder.py

import time
from openai import OpenAI
from config.settings import settings


class Embedder:
    """
    Converts text into vectors using OpenAI text-embedding-3-small.

    What is a vector?
    A vector is a list of 1536 numbers. Each number represents
    a dimension of meaning. You cannot interpret individual numbers
    ("dimension 42 = medical-ness") but the overall pattern encodes
    semantic meaning. Two texts with similar meaning produce vectors
    that point in roughly the same direction in 1536-dimensional space.

    Why text-embedding-3-small specifically?
    - 1536 dimensions: enough accuracy for medical text retrieval
    - Cost: $0.02 per million tokens (~$0.04 to embed 10,000 abstracts)
    - Speed: fast enough for batch ingestion
    - It is the same model Pinecone expects when we set dimension=1536

    Why OpenAI for embeddings?
    We use OpenAI because:
    - No GPU required — runs on any machine
    - Consistent quality — same model every time
    - Simple API — one function call per batch
    """

    def __init__(self):
        # OpenAI client reads OPENAI_API_KEY from your .env automatically
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model  = settings.EMBED_MODEL    # "text-embedding-3-small"
        self.dim    = settings.EMBED_DIM      # 1536

    def embed_one(self, text):
        """
        Embed a single text string into one vector.
        Used at query time — when a user types a question,
        we embed that question before searching Pinecone.

        Returns: list of 1536 floats
        """
        cleaned = self._clean(text)
        response = self.client.embeddings.create(
            model=self.model,
            input=cleaned,
        )
        return response.data[0].embedding

    def embed_many(self, texts, batch_size=100):
        """
        Embed a list of texts efficiently in batches.
        Used during ingestion — we have hundreds of chunks to embed.

        Why batch_size=100?
        OpenAI accepts up to 2048 inputs per API call, but
        100 is a safe size that avoids timeouts and rate limit
        errors while still being much faster than one-by-one.

        Args:
            texts:      list of strings to embed
            batch_size: how many texts per API call

        Returns: list of vectors, same order as input texts
        """
        all_vectors = []
        cleaned     = [self._clean(t) for t in texts]
        total       = len(cleaned)

        print(f"[Embedder] Embedding {total} texts in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch     = cleaned[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            print(f"[Embedder] Batch {batch_num}/{total_batches} ({len(batch)} texts)...")

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                # Sort by index to guarantee order matches input
                # (API usually returns in order but we sort to be safe)
                items    = sorted(response.data, key=lambda x: x.index)
                vectors  = [item.embedding for item in items]
                all_vectors.extend(vectors)

            except Exception as e:
                print(f"[Embedder] Batch {batch_num} failed: {e}")
                print(f"[Embedder] Falling back to zero vectors for this batch")
                # Zero vectors won't match anything in Pinecone
                # Safe fallback — bad chunks won't pollute search results
                all_vectors.extend([[0.0] * self.dim] * len(batch))

            # Small pause between batches to respect rate limits
            # OpenAI rate limit: 3000 requests/min on free tier
            time.sleep(0.1)

        print(f"[Embedder] Done. {len(all_vectors)} vectors produced.")
        return all_vectors

    def cosine_similarity(self, vec_a, vec_b):
        """
        Measures how similar two vectors are.
        Returns a score from -1.0 to 1.0:
            1.0  = identical meaning
            0.0  = completely unrelated
           -1.0  = opposite meaning (rare in practice)

        This is the same math Pinecone uses internally
        when you search for similar vectors.

        We include this here so you can test and understand
        similarity before Pinecone is even involved.

        Formula:
            cosine similarity = (A · B) / (|A| × |B|)
            where A · B is the dot product
            and |A|, |B| are the magnitudes (lengths) of each vector
        """
        # Dot product: multiply matching dimensions, sum them up
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))

        # Magnitude: square root of sum of squares
        magnitude_a = sum(a * a for a in vec_a) ** 0.5
        magnitude_b = sum(b * b for b in vec_b) ** 0.5

        # Avoid division by zero if either vector is all zeros
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def _clean(self, text):
        """
        Prepares text before embedding.

        Why truncate?
        text-embedding-3-small has a hard limit of 8192 tokens.
        ~1 token = 0.75 words, so 8192 tokens ≈ 6144 words.
        Anything longer gets silently truncated by the API anyway,
        so we truncate ourselves first at 6000 words to be safe
        and to avoid paying for tokens that get cut off.

        Why strip whitespace?
        Extra spaces and newlines inflate token count without
        adding meaning. A clean string embeds more efficiently.
        """
        # Collapse multiple spaces/newlines into single spaces
        text = " ".join(text.split())

        # Truncate if too long
        words = text.split()
        if len(words) > 6000:
            text = " ".join(words[:6000])

        return text.strip()