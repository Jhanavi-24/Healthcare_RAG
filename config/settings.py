import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Pinecone
    PINECONE_API_KEY  = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX    = os.getenv("PINECONE_INDEX_NAME", "healthcare-rag")
    PINECONE_CLOUD    = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION   = os.getenv("PINECONE_REGION", "us-east-1")

    # OpenAI
    OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
    EMBED_MODEL       = "text-embedding-3-small"
    EMBED_DIM         = 1536
    CHAT_MODEL        = "gpt-4o-mini"

    # Data source URLs
    PUBMED_URL        = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    TRIALS_URL        = "https://clinicaltrials.gov/api/v2/studies"
    FDA_URL           = "https://api.fda.gov/drug"
    NCBI_EMAIL        = os.getenv("NCBI_EMAIL", "researcher@example.com")

    # Ingestion
    CHUNK_SIZE        = 450
    BATCH_SIZE        = 100

    # Retrieval
    TOP_K             = 5
    MIN_SCORE         = 0.70

    # Evidence weights
    EVIDENCE_WEIGHTS  = {
        "systematic_review": 1.00,
        "rct":               0.85,
        "clinical_trial":    0.80,
        "guideline":         0.80,
        "fda_label":         0.75,
        "cohort_study":      0.65,
        "abstract":          0.55,
        "case_report":       0.40,
        "unknown":           0.50,
    }

settings = Settings()