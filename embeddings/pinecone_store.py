# embeddings/pinecone_store.py

from pinecone import Pinecone, ServerlessSpec
from config.settings import settings


class PineconeStore:
    """
    Manages the Pinecone vector index.

    Key concepts before reading this code:

    INDEX
    An index is like a database table, but instead of rows with
    text columns, it stores vectors (lists of numbers). Every
    vector in an index must have the same number of dimensions —
    ours is 1536 to match text-embedding-3-small.

    UPSERT
    "Upsert" = insert if new, update if ID already exists.
    This means you can re-run ingestion safely — no duplicate
    vectors pile up. Same chunk ID = same slot in the index.

    COSINE SIMILARITY
    When you search, Pinecone compares your query vector against
    every stored vector using cosine similarity (same math we
    built in Component 3). It returns the top-k closest matches
    in milliseconds, even across millions of vectors.

    METADATA
    Each vector can carry a dict of extra info — title, year,
    source, URL, evidence type. This is how we know WHERE a
    retrieved chunk came from so we can show citations.

    SERVERLESS
    We use Pinecone's serverless tier — no servers to manage,
    scales automatically, free tier supports 1 index up to 2GB.
    """

    def __init__(self):
        # Initialize Pinecone client with your API key
        self.pc         = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX
        self.dimension  = settings.EMBED_DIM   # must match embedding model (1536)
        self._index     = None                 # lazy-loaded below

    @property
    def index(self):
        """
        Lazy-load the index object.

        Why lazy?
        Creating the Pinecone client is instant, but connecting
        to the index makes a network call. We only do that when
        we actually need to read/write, not on every import.
        """
        if self._index is None:
            self._index = self.pc.Index(self.index_name)
        return self._index

    def create_index(self):
        """
        Creates the Pinecone index if it doesn't already exist.
        Run this ONCE via scripts/setup.py before ingesting data.

        Why ServerlessSpec?
        Pinecone has two modes:
        - Pod-based: you pay for dedicated hardware (expensive)
        - Serverless: Pinecone manages infrastructure, you pay
          per query/storage (free tier available, perfect for us)

        Why metric="cosine"?
        Cosine similarity is best for text — it measures the
        angle between vectors regardless of their magnitude.
        A short abstract and a long one about the same topic
        will still score high similarity with cosine.

        Other options: "euclidean" (distance in space, worse for
        text), "dotproduct" (faster but requires normalized vectors).
        """
        existing_indexes = [i.name for i in self.pc.list_indexes()]

        if self.index_name in existing_indexes:
            print(f"[Pinecone] Index '{self.index_name}' already exists. Skipping creation.")
            return

        print(f"[Pinecone] Creating index '{self.index_name}'...")
        print(f"[Pinecone] Dimension: {self.dimension}, Metric: cosine")

        self.pc.create_index(
            name      = self.index_name,
            dimension = self.dimension,
            metric    = "cosine",
            spec      = ServerlessSpec(
                cloud  = settings.PINECONE_CLOUD,   # "aws"
                region = settings.PINECONE_REGION,  # "us-east-1"
            )
        )
        print(f"[Pinecone] Index created successfully.")

    def upsert(self, chunks, vectors):
        """
        Store chunks and their vectors in Pinecone.

        Args:
            chunks:  list of Chunk objects (from chunker.py)
            vectors: list of vectors in same order as chunks

        Why batch_size=100?
        Pinecone's upsert API accepts up to 100 vectors per call.
        Sending more causes an error. We batch automatically so
        you never have to think about this limit.

        Returns:
            Total number of vectors stored
        """
        assert len(chunks) == len(vectors), (
            f"Mismatch: {len(chunks)} chunks but {len(vectors)} vectors"
        )

        total      = 0
        batch_size = settings.BATCH_SIZE   # 100

        for i in range(0, len(chunks), batch_size):
            batch_chunks  = chunks[i : i + batch_size]
            batch_vectors = vectors[i : i + batch_size]

            # Build the records Pinecone expects
            # Each record: {"id": str, "values": list[float], "metadata": dict}
            records = []
            for chunk, vector in zip(batch_chunks, batch_vectors):
                metadata = self._clean_metadata(chunk.metadata)

                # Store truncated text in metadata so we can show
                # the actual content when we retrieve it later.
                # Pinecone metadata limit: 40KB per vector.
                # 800 chars is safe and gives enough context.
                metadata["text"] = chunk.text[:800]

                records.append({
                    "id":       chunk.id,
                    "values":   vector,
                    "metadata": metadata,
                })

            try:
                self.index.upsert(vectors=records)
                total += len(records)
                print(f"[Pinecone] Stored {total}/{len(chunks)} vectors...")
            except Exception as e:
                print(f"[Pinecone] Upsert error on batch {i//batch_size + 1}: {e}")

        print(f"[Pinecone] Done. {total} vectors stored.")
        return total

    def search(self, query_vector, top_k=None, filters=None):
        """
        Find the most similar vectors to a query vector.

        This is the core of RAG retrieval — we embed the user's
        question and find which stored chunks are most similar.

        Args:
            query_vector: embedded question (list of 1536 floats)
            top_k:        how many results to return (default: 5)
            filters:      optional metadata filter dict, e.g.:
                          {"source": {"$in": ["pubmed"]}}
                          {"year": {"$gte": 2020}}

        Returns:
            list of dicts: [{"id": str, "score": float, "metadata": dict}]
            sorted by score descending (best match first)

        How Pinecone searches:
        It does NOT compare your query to every single vector
        one-by-one (that would be slow for millions of vectors).
        It uses Approximate Nearest Neighbor (ANN) search —
        a technique that finds the closest vectors in milliseconds
        by intelligently pruning the search space.
        """
        top_k = top_k or settings.TOP_K

        query_params = {
            "vector":           query_vector,
            "top_k":            top_k,
            "include_metadata": True,   # we need metadata to show citations
        }

        if filters:
            query_params["filter"] = filters

        response = self.index.query(**query_params)

        # Convert Pinecone response objects to plain dicts
        return [
            {
                "id":       match.id,
                "score":    match.score,       # cosine similarity 0-1
                "metadata": match.metadata,
            }
            for match in response.matches
        ]

    def stats(self):
        """
        Returns index statistics.
        Most useful field: total_vector_count — how many
        vectors are currently stored in the index.
        """
        return self.index.describe_index_stats()

    def delete_all(self):
        """
        Deletes all vectors from the index.
        Useful if you want to re-ingest everything from scratch.
        Does NOT delete the index itself — just clears its contents.
        """
        print(f"[Pinecone] Deleting all vectors from '{self.index_name}'...")
        self.index.delete(delete_all=True)
        print(f"[Pinecone] All vectors deleted.")

    def _clean_metadata(self, metadata):
        """
        Pinecone only accepts specific types as metadata values:
            str, int, float, bool, list[str]

        This method converts anything else to a safe type so
        upsert never fails due to a metadata type error.

        Common problems this prevents:
        - None values → converted to ""
        - Nested dicts → converted to str
        - Mixed-type lists → converted to list[str]
        """
        clean = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            elif isinstance(value, list):
                # Convert all list items to strings
                clean[key] = [str(item) for item in value]
            elif value is None:
                clean[key] = ""
            else:
                clean[key] = str(value)
        return clean