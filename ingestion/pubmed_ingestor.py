# ingestion/pubmed_ingestor.py

import time
import requests
import xml.etree.ElementTree as ET


class PubMedArticle:
    """
    Holds one research article from PubMed.
    
    Why a class instead of a dict?
    A class gives you named attributes (article.title, article.abstract)
    instead of error-prone string keys (article["titl"] — typo, crashes at runtime).
    It also lets us add helper properties like evidence_type and text.
    """

    def __init__(self, pmid, title, abstract, authors,
                 journal, year, pub_types, mesh_terms, doi=""):
        self.pmid       = pmid        # PubMed unique ID e.g. "38291453"
        self.title      = title
        self.abstract   = abstract
        self.authors    = authors     # list of strings e.g. ["Smith J", "Jones A"]
        self.journal    = journal
        self.year       = year        # int e.g. 2023
        self.pub_types  = pub_types   # list e.g. ["Randomized Controlled Trial"]
        self.mesh_terms = mesh_terms  # list e.g. ["Diabetes Mellitus", "Metformin"]
        self.doi        = doi

    @property
    def evidence_type(self):
        """
        Maps PubMed's publication type labels to our own evidence categories.
        We use this later when scoring how trustworthy a chunk is.
        
        Why does this matter?
        A systematic review (evidence_type = "systematic_review") should rank
        higher than a single case report when answering a clinical question.
        This property lets the confidence scorer treat them differently.
        """
        pt = [p.lower() for p in self.pub_types]

        if any("systematic review" in p or "meta-analysis" in p for p in pt):
            return "systematic_review"
        if any("randomized controlled trial" in p for p in pt):
            return "rct"
        if any("clinical trial" in p for p in pt):
            return "clinical_trial"
        if any("practice guideline" in p or "guideline" in p for p in pt):
            return "guideline"
        if any("case report" in p or "case reports" in p for p in pt):
            return "case_report"
        return "abstract"

    @property
    def text(self):
        """
        The text we will embed in Component 3.
        We combine title + abstract because:
        - Title alone is too short (loses context)
        - Abstract alone sometimes drops the key topic that's in the title
        - Together they give the embedding model the full picture
        """
        return f"Title: {self.title}\n\nAbstract: {self.abstract}"

    def metadata(self):
        """
        Extra info stored alongside the vector in Pinecone (Component 4).
        When we retrieve a chunk, this is how we know where it came from,
        what year it was published, and what URL to show the user.
        
        Pinecone metadata rules: values must be str, int, float, bool, or list[str].
        No nested dicts. That is why authors is joined into one string.
        """
        return {
            "source":        "pubmed",
            "pmid":          self.pmid,
            "title":         self.title[:400],          # Pinecone has a metadata size limit
            "authors":       "; ".join(self.authors[:3]),
            "journal":       self.journal,
            "year":          self.year,
            "evidence_type": self.evidence_type,
            "doi":           self.doi,
            "url":           f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/",
        }

    def __repr__(self):
        """Makes print(article) show something useful instead of <object at 0x...>"""
        return f"PubMedArticle(pmid={self.pmid}, year={self.year}, type={self.evidence_type}, title={self.title[:60]}...)"


class PubMedIngestor:
    """
    Fetches articles from PubMed using NCBI E-utilities API.
    
    Why this API?
    - Completely free, no key required
    - Returns structured XML with titles, abstracts, authors, dates
    - Covers 36 million+ biomedical articles
    
    The API works in two steps:
    Step 1 — esearch: "give me IDs of articles matching this query" → returns PMIDs
    Step 2 — efetch: "give me full content for these IDs" → returns XML
    
    We always do both steps. You cannot skip step 1 and jump straight to content.
    """

    # Base URL for all NCBI E-utilities calls
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, email="researcher@example.com"):
        """
        email: NCBI asks you to include your email in requests.
        It is not required, but it is polite — if your script
        misbehaves they can contact you instead of blocking your IP.
        """
        self.email = email
        self.delay = 0.4    # seconds to wait between API calls
                            # NCBI rate limit: 3 requests/sec without a key
                            # 0.4s gap = safe (2.5 req/sec)

    def search(self, query, max_results=100):
        """
        Main entry point. Searches PubMed and returns a list of PubMedArticle objects.
        
        Args:
            query:       e.g. "type 2 diabetes first line treatment"
            max_results: how many articles to fetch (start small — 100 is fine)
        
        Returns:
            list of PubMedArticle objects
        
        Example:
            ingestor = PubMedIngestor(email="you@email.com")
            articles = ingestor.search("metformin type 2 diabetes", max_results=50)
        """
        print(f"\n[PubMed] Searching for: '{query}'")
        print(f"[PubMed] Max results: {max_results}")

        # Step 1: Get article IDs
        pmids = self._search_pmids(query, max_results)
        if not pmids:
            print("[PubMed] No results found.")
            return []

        # Step 2: Get full article content for those IDs
        articles = self._fetch_articles(pmids)

        # Filter out articles with no abstract — useless for RAG
        articles_with_abstract = [a for a in articles if a.abstract.strip()]
        print(f"[PubMed] Done. {len(articles_with_abstract)} articles with abstracts.")
        return articles_with_abstract

    def _search_pmids(self, query, max_results):
        """
        Step 1: Call esearch to get a list of PubMed IDs (PMIDs).
        
        Returns a list of strings like ["38291453", "37845621", ...]
        """
        print(f"[PubMed] Step 1/2 — searching index...")

        params = {
            "db":      "pubmed",       # which NCBI database to search
            "term":    query,          # the search query
            "retmax":  max_results,    # max IDs to return
            "retmode": "json",         # we want JSON for the ID list (easier to parse)
            "sort":    "relevance",    # most relevant first
            "email":   self.email,
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=params,
                timeout=30             # fail after 30s instead of hanging forever
            )
            response.raise_for_status()  # raises an error if HTTP status is 4xx or 5xx
        except requests.RequestException as e:
            print(f"[PubMed] Search request failed: {e}")
            return []

        data  = response.json()
        pmids = data.get("esearchresult", {}).get("idlist", [])
        print(f"[PubMed] Found {len(pmids)} article IDs")

        time.sleep(self.delay)  # be polite to NCBI servers
        return pmids

    def _fetch_articles(self, pmids):
        """
        Step 2: Call efetch to get full XML content for a list of PMIDs.
        
        We fetch in batches of 100 because:
        - The API has URL length limits
        - If one batch fails, we still have results from other batches
        - It shows a progress indicator for large fetches
        """
        print(f"[PubMed] Step 2/2 — fetching {len(pmids)} articles...")

        articles    = []
        batch_size  = 100

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            print(f"[PubMed] Fetching batch {batch_num} ({len(batch)} articles)...")

            params = {
                "db":      "pubmed",
                "id":      ",".join(batch),  # comma-separated list of IDs
                "rettype": "xml",
                "retmode": "xml",            # XML gives us the most structured data
                "email":   self.email,
            }

            try:
                response = requests.get(
                    f"{self.BASE_URL}/efetch.fcgi",
                    params=params,
                    timeout=60              # bigger timeout — fetching full XML takes longer
                )
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"[PubMed] Fetch batch {batch_num} failed: {e}. Skipping.")
                continue

            # Parse the XML response into PubMedArticle objects
            batch_articles = self._parse_xml(response.text)
            articles.extend(batch_articles)
            print(f"[PubMed] Parsed {len(batch_articles)} articles from batch {batch_num}")

            time.sleep(self.delay)

        return articles

    def _parse_xml(self, xml_text):
        """
        Parses the raw XML string from efetch into a list of PubMedArticle objects.
        
        Why XML and not JSON?
        PubMed's efetch returns much richer data in XML — including structured
        abstracts (BACKGROUND, METHODS, RESULTS sections), MeSH terms, multiple
        author affiliations, and article identifiers. The JSON option loses most of this.
        
        xml.etree.ElementTree is Python's built-in XML parser — no extra install needed.
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            print(f"[PubMed] XML parse error: {e}. Skipping batch.")
            return []

        articles = []

        # Each <PubmedArticle> tag is one paper
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                article = self._parse_single_article(article_elem)
                if article:
                    articles.append(article)
            except Exception as e:
                # Don't crash the whole batch over one bad article
                pmid = article_elem.findtext(".//PMID", default="unknown")
                print(f"[PubMed] Skipping article PMID={pmid}: {e}")

        return articles

    def _parse_single_article(self, elem):
        """
        Extracts fields from one <PubmedArticle> XML element.
        
        Helper functions defined inside to keep things readable:
        - get_text(path): find one element, return its text
        - get_all_texts(path): find all matching elements, return list of texts
        """

        def get_text(path):
            """Find a single element by XPath and return its full text content."""
            node = elem.find(path)
            if node is None:
                return ""
            # itertext() handles mixed content like <b>bold</b> text within a tag
            return "".join(node.itertext()).strip()

        def get_all_texts(path):
            """Find all matching elements and return a list of their text contents."""
            return [
                "".join(node.itertext()).strip()
                for node in elem.findall(path)
            ]

        # ── Abstract ─────────────────────────────────────────────────────────
        # Abstracts can be plain text OR structured (BACKGROUND / METHODS / RESULTS)
        # We handle both cases and join structured sections with their labels
        abstract_parts = []
        for abstract_text_elem in elem.findall(".//AbstractText"):
            label   = abstract_text_elem.get("Label")   # e.g. "BACKGROUND"
            content = "".join(abstract_text_elem.itertext()).strip()
            if label:
                abstract_parts.append(f"{label}: {content}")
            else:
                abstract_parts.append(content)
        abstract = "\n".join(abstract_parts)

        # ── Year ──────────────────────────────────────────────────────────────
        # PubDate can be <Year>2023</Year> or <MedlineDate>2023 Jan-Feb</MedlineDate>
        year_str = get_text(".//PubDate/Year") or get_text(".//PubDate/MedlineDate")
        try:
            year = int(year_str[:4])   # take first 4 chars to handle "2023 Jan-Feb"
        except (ValueError, TypeError):
            year = 0

        # ── Authors ───────────────────────────────────────────────────────────
        authors = []
        for author_elem in elem.findall(".//Author"):
            last  = author_elem.findtext("LastName")  or ""
            first = author_elem.findtext("ForeName")  or ""
            if last:
                authors.append(f"{last} {first}".strip())

        # ── DOI ───────────────────────────────────────────────────────────────
        doi = ""
        for article_id_elem in elem.findall(".//ArticleId"):
            if article_id_elem.get("IdType") == "doi":
                doi = article_id_elem.text or ""
                break

        return PubMedArticle(
            pmid       = get_text(".//PMID"),
            title      = get_text(".//ArticleTitle"),
            abstract   = abstract,
            authors    = authors,
            journal    = get_text(".//Journal/Title"),
            year       = year,
            pub_types  = get_all_texts(".//PublicationType"),
            mesh_terms = get_all_texts(".//MeshHeading/DescriptorName"),
            doi        = doi,
        )