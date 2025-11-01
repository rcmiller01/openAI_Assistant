-- Advanced search functions for hybrid BM25 + vector search
-- Run with: psql -U opa -d opa -f 002_hybrid_search_functions.sql

-- BM25 scoring function for text search
CREATE OR REPLACE FUNCTION bm25_score(
    query_text TEXT,
    doc_text TEXT,
    k1 FLOAT DEFAULT 1.5,
    b FLOAT DEFAULT 0.75
) RETURNS FLOAT AS $$
DECLARE
    avg_doc_len FLOAT;
    doc_len INT;
    term TEXT;
    term_freq INT;
    doc_freq INT;
    total_docs INT;
    idf FLOAT;
    tf_component FLOAT;
    score FLOAT := 0;
BEGIN
    -- Get average document length
    SELECT AVG(length(text)) INTO avg_doc_len FROM memory_items;
    doc_len := length(doc_text);
    total_docs := (SELECT COUNT(*) FROM memory_items);
    
    -- For each term in query
    FOR term IN SELECT unnest(string_to_array(lower(query_text), ' '))
    LOOP
        -- Term frequency in document
        term_freq := (
            SELECT COUNT(*)
            FROM unnest(string_to_array(lower(doc_text), ' ')) AS word
            WHERE word = term
        );
        
        IF term_freq > 0 THEN
            -- Document frequency (how many docs contain term)
            doc_freq := (
                SELECT COUNT(*)
                FROM memory_items
                WHERE lower(text) LIKE '%' || term || '%'
            );
            
            -- IDF calculation
            idf := ln((total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1);
            
            -- TF component with length normalization
            tf_component := (term_freq * (k1 + 1)) / 
                           (term_freq + k1 * (1 - b + b * (doc_len / avg_doc_len)));
            
            score := score + (idf * tf_component);
        END IF;
    END LOOP;
    
    RETURN score;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Hybrid search combining BM25 + vector similarity
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding VECTOR(384),
    query_tags TEXT[] DEFAULT '{}',
    k INT DEFAULT 10,
    bm25_weight FLOAT DEFAULT 0.5,
    vector_weight FLOAT DEFAULT 0.5
) RETURNS TABLE(
    id VARCHAR(64),
    text TEXT,
    tags TEXT[],
    created_at TIMESTAMPTZ,
    bm25_score FLOAT,
    vector_score FLOAT,
    combined_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.text,
        m.tags,
        m.created_at,
        bm25_score(query_text, m.text) AS bm25_score,
        (1 - (m.embedding <=> query_embedding)) AS vector_score,  -- cosine similarity
        (bm25_weight * bm25_score(query_text, m.text) + 
         vector_weight * (1 - (m.embedding <=> query_embedding))) AS combined_score
    FROM memory_items m
    WHERE
        (query_tags = '{}' OR m.tags && query_tags)  -- Tag filter if provided
        AND m.embedding IS NOT NULL  -- Only search items with embeddings
    ORDER BY combined_score DESC
    LIMIT k;
END;
$$ LANGUAGE plpgsql;

-- Pure vector search (faster for semantic similarity)
CREATE OR REPLACE FUNCTION vector_search(
    query_embedding VECTOR(384),
    query_tags TEXT[] DEFAULT '{}',
    k INT DEFAULT 10
) RETURNS TABLE(
    id VARCHAR(64),
    text TEXT,
    tags TEXT[],
    created_at TIMESTAMPTZ,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.text,
        m.tags,
        m.created_at,
        (1 - (m.embedding <=> query_embedding)) AS similarity
    FROM memory_items m
    WHERE
        (query_tags = '{}' OR m.tags && query_tags)
        AND m.embedding IS NOT NULL
    ORDER BY m.embedding <=> query_embedding
    LIMIT k;
END;
$$ LANGUAGE plpgsql;

-- Pure BM25 search (faster for keyword matching)
CREATE OR REPLACE FUNCTION bm25_search(
    query_text TEXT,
    query_tags TEXT[] DEFAULT '{}',
    k INT DEFAULT 10
) RETURNS TABLE(
    id VARCHAR(64),
    text TEXT,
    tags TEXT[],
    created_at TIMESTAMPTZ,
    score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.text,
        m.tags,
        m.created_at,
        bm25_score(query_text, m.text) AS score
    FROM memory_items m
    WHERE
        (query_tags = '{}' OR m.tags && query_tags)
        AND lower(m.text) LIKE '%' || lower(query_text) || '%'  -- Basic filter
    ORDER BY score DESC
    LIMIT k;
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON FUNCTION bm25_score IS 'Calculate BM25 relevance score for text search';
COMMENT ON FUNCTION hybrid_search IS 'Combine BM25 keyword + vector semantic search with weights';
COMMENT ON FUNCTION vector_search IS 'Pure vector similarity search using cosine distance';
COMMENT ON FUNCTION bm25_search IS 'Pure BM25 keyword search for exact matches';
