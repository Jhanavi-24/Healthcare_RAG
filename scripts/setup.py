# scripts/setup.py

import sys
sys.path.insert(0, ".")

from config.settings import settings
from embeddings.pinecone_store import PineconeStore


def main():
    print("=" * 60)
    print("Healthcare RAG — Pinecone Setup")
    print("=" * 60)

    # Check API keys are present
    missing = []
    if not settings.PINECONE_API_KEY or "your_" in settings.PINECONE_API_KEY:
        missing.append("PINECONE_API_KEY")
    if not settings.OPENAI_API_KEY or "your_" in settings.OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        print("\nMissing keys in .env:")
        for k in missing:
            print(f"  - {k}")
        sys.exit(1)

    print("\nAll API keys found.")

    # Create the index
    store = PineconeStore()
    store.create_index()

    # Show current stats
    try:
        st    = store.stats()
        count = st.get("total_vector_count", 0)
        print(f"\nIndex name:      {settings.PINECONE_INDEX}")
        print(f"Dimension:       {settings.EMBED_DIM}")
        print(f"Vectors stored:  {count}")
    except Exception as e:
        print(f"Could not fetch stats: {e}")

    print("\nSetup complete.")
    print("Next: python3 test_component4.py")


if __name__ == "__main__":
    main()