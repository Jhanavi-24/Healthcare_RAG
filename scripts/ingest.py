# scripts/ingest.py

"""
Ingest medical data into Pinecone.

Usage:
  python3 scripts/ingest.py --query "diabetes treatment" --max 200
  python3 scripts/ingest.py --query "hypertension management" --max 150
  python3 scripts/ingest.py --query "sepsis protocol" --max 100
"""

import sys
import argparse
sys.path.insert(0, ".")

from ingestion.pubmed_ingestor import PubMedIngestor
from ingestion.chunker import Chunker
from embeddings.embedder import Embedder
from embeddings.pinecone_store import PineconeStore


def ingest_pubmed(query, max_results, chunker, embedder, store):
    """
    Full ingestion pipeline for one PubMed query:
    fetch → chunk → embed → store
    """
    print(f"\n{'='*60}")
    print(f"Ingesting: '{query}'")
    print(f"{'='*60}")

    # Step 1: Fetch articles from PubMed
    ingestor = PubMedIngestor(email="your_email@example.com")
    articles = ingestor.search(query, max_results=max_results)

    if not articles:
        print(f"No articles found for '{query}'. Skipping.")
        return 0

    # Step 2: Chunk all articles
    print(f"\nChunking {len(articles)} articles...")
    all_chunks = []
    for article in articles:
        all_chunks.extend(chunker.chunk_pubmed(article))
    print(f"Produced {len(all_chunks)} chunks")

    # Step 3: Embed all chunks
    print(f"\nEmbedding {len(all_chunks)} chunks...")
    texts   = [c.text for c in all_chunks]
    vectors = embedder.embed_many(texts)

    # Step 4: Store in Pinecone
    print(f"\nStoring in Pinecone...")
    stored = store.upsert(all_chunks, vectors)

    print(f"\nDone. {stored} vectors stored for '{query}'")
    return stored


def main():
    parser = argparse.ArgumentParser(description="Ingest PubMed data into Pinecone")
    parser.add_argument("--query", type=str, required=True,
                        help="PubMed search query")
    parser.add_argument("--max", type=int, default=200,
                        help="Max articles to fetch (default: 200)")
    args = parser.parse_args()

    chunker  = Chunker()
    embedder = Embedder()
    store    = PineconeStore()

    total = ingest_pubmed(args.query, args.max, chunker, embedder, store)

    # Show final index stats
    stats = store.stats()
    print(f"\n{'='*60}")
    print(f"Total vectors in index: {stats.get('total_vector_count', '?')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()