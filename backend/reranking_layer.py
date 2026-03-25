"""
Reranking Layer for SoloAnalyst
Implements two-stage reranking to improve source quality
Stage 1: LightGBM-based fast filtering
Stage 2: Cross-encoder semantic reranking (optional, for high-value queries)
"""

import os
import re
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

# Try to import ML libraries, fall back to heuristic mode if not available
try:
    import lightgbm as lgb
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("[RERANK] LightGBM not available, using heuristic mode")


@dataclass
class Source:
    """Unified source representation"""
    title: str
    url: str
    content: str
    source: str  # Exa, Tavily, Brave, Scrapling, etc.
    score: float = 0.0  # Initial retrieval score if available

    def __lt__(self, other):
        return self.score < getattr(other, 'score', 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'url': self.url,
            'content': self.content,
            'source': self.source,
            'score': self.score
        }


class FeatureExtractor:
    """Extract features from sources for reranking"""
    
    # Domain authority scores (simplified, could be expanded)
    HIGH_AUTHORITY_DOMAINS = {
        'crunchbase.com': 1.0,
        'linkedin.com': 0.9,
        'bloomberg.com': 0.95,
        'reuters.com': 0.95,
        'forbes.com': 0.85,
        'techcrunch.com': 0.8,
        'venturebeat.com': 0.8,
        'medium.com': 0.6,
        'substack.com': 0.6,
        'github.com': 0.85,
        'glassdoor.com': 0.75,
        'indeed.com': 0.75,
        'pitchbook.com': 0.9,
        'tracxn.com': 0.9,
        'cbinsights.com': 0.9,
    }
    
    LOW_QUALITY_PATTERNS = [
        r'login|signin|password|forgot',
        r'404|not found|error page',
        r'index of|directory listing',
        r'suspended|domain for sale',
    ]
    
    def __init__(self):
        self.low_quality_regex = re.compile('|'.join(self.LOW_QUALITY_PATTERNS), re.IGNORECASE)
    
    def extract_features(self, source: Source, query: str) -> np.ndarray:
        """Extract feature vector for a source"""
        features = []
        
        # Handle None values gracefully
        title = source.title or ""
        content = source.content or ""
        query = query or ""
        url = source.url or ""
        
        # 1. Content Quality Features
        content_len = len(content)
        features.append(min(content_len / 5000, 1.0))  # Normalized content length
        features.append(1.0 if content_len > 500 else 0.0)  # Has substantial content
        features.append(1.0 if content_len > 2000 else 0.0)  # Has detailed content
        
        # 2. Source Authority Features
        domain = self._extract_domain(url)
        authority_score = self.HIGH_AUTHORITY_DOMAINS.get(domain, 0.3)
        features.append(authority_score)
        features.append(1.0 if authority_score > 0.7 else 0.0)  # High authority flag
        
        # 3. Query Relevance Features
        query_terms = set(query.lower().split())
        title_match = len(set(title.lower().split()) & query_terms) / max(len(query_terms), 1)
        content_match = self._count_query_matches(content.lower(), query_terms)
        features.append(title_match)
        features.append(min(content_match / 10, 1.0))  # Normalized content matches
        
        # 4. Quality Signals
        features.append(0.0 if self.low_quality_regex.search(title) else 1.0)
        features.append(0.0 if self.low_quality_regex.search(content[:500]) else 1.0)
        features.append(1.0 if title and len(title) > 10 else 0.0)
        
        # 5. Source Type Features
        source_scores = {
            'Exa': 0.9,      # Neural search, high quality
            'Tavily': 0.85,  # AI search engine
            'Brave': 0.7,    # General search
            'Scrapling': 0.95,  # Official site
            'Apify': 0.9,    # Structured data
        }
        features.append(source_scores.get(source.source, 0.5))
        
        # 6. URL Features
        url_lower = url.lower()
        features.append(1.0 if '/about' in url_lower else 0.0)
        features.append(1.0 if '/team' in url_lower else 0.0)
        features.append(1.0 if '/product' in url_lower else 0.0)
        features.append(1.0 if re.search(r'/20\d\d/', url) else 0.0)  # Has year (news)
        
        # 7. Content Freshness (if detectable)
        freshness_score = self._estimate_freshness(content)
        features.append(freshness_score)
        
        return np.array(features, dtype=np.float32)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        url = url.replace('https://', '').replace('http://', '')
        domain = url.split('/')[0]
        return domain.replace('www.', '')
    
    def _count_query_matches(self, content: str, query_terms: set) -> int:
        """Count how many query terms appear in content"""
        content_words = set(content.split())
        return len(query_terms & content_words)
    
    def _estimate_freshness(self, content: str) -> float:
        """Estimate content freshness based on date mentions"""
        # Look for recent years (2024, 2025, 2026)
        recent_years = re.findall(r'\b(202[4-6])\b', content)
        if recent_years:
            return 1.0
        # Look for any year
        any_years = re.findall(r'\b(20\d{2})\b', content)
        if any_years:
            return 0.5
        return 0.3  # Unknown freshness


class RerankingService:
    """Main reranking service"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.feature_extractor = FeatureExtractor()
        self.model = None
        
        if ML_AVAILABLE and model_path and os.path.exists(model_path):
            try:
                self.model = lgb.Booster(model_file=model_path)
                print(f"[RERANK] Loaded model from {model_path}")
            except Exception as e:
                print(f"[RERANK] Failed to load model: {e}, using heuristic mode")
    
    def rerank(self, 
               query: str, 
               sources: List[Dict[str, Any]], 
               user_context: Optional[Dict] = None,
               top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Rerank sources using two-stage approach
        
        Args:
            query: Search query
            sources: List of source dictionaries
            user_context: Optional user context (company, sector, etc.)
            top_k: Number of top sources to return
        
        Returns:
            Reranked list of sources
        """
        if not sources:
            return []
        
        # Convert to Source objects
        source_objects = [Source(**s) if isinstance(s, dict) else s for s in sources]
        
        # Stage 1: Fast filtering with LightGBM or heuristics
        stage1_scores = self._stage1_score(query, source_objects)
        
        # Keep top 20 for Stage 2 (or all if less than 20)
        top_indices = np.argsort(stage1_scores)[::-1][:min(20, len(source_objects))]
        stage2_candidates = [source_objects[i] for i in top_indices]
        
        # Stage 2: Semantic reranking (if we have cross-encoder, otherwise skip)
        if len(stage2_candidates) > top_k:
            final_sources = self._stage2_rerank(query, stage2_candidates, top_k)
        else:
            final_sources = stage2_candidates[:top_k]
        
        # Convert back to dicts and add rerank scores
        result = []
        for i, src in enumerate(final_sources):
            src_dict = src.to_dict() if hasattr(src, 'to_dict') else src
            src_dict['rerank_score'] = float(len(final_sources) - i) / len(final_sources)
            src_dict['rerank_position'] = i + 1
            result.append(src_dict)
        
        return result
    
    def _stage1_score(self, query: str, sources: List[Source]) -> np.ndarray:
        """Stage 1: Fast feature-based scoring"""
        features = np.array([self.feature_extractor.extract_features(s, query) for s in sources])
        
        if self.model is not None and ML_AVAILABLE:
            # Use trained LightGBM model
            scores = self.model.predict(features)
        else:
            # Heuristic: weighted sum of features
            # These weights are tuned for investment research
            weights = np.array([
                0.10,  # content length
                0.05,  # has content
                0.05,  # has detailed content
                0.20,  # domain authority
                0.10,  # high authority flag
                0.15,  # title match
                0.10,  # content match
                0.05,  # title quality
                0.05,  # content quality
                0.05,  # has title
                0.05,  # source type
                0.03,  # about page
                0.03,  # team page
                0.03,  # product page
                0.02,  # has date
                0.05,  # freshness
            ])
            scores = features @ weights
        
        return scores
    
    def _stage2_rerank(self, query: str, sources: List[Source], top_k: int) -> List[Source]:
        """Stage 2: Semantic reranking with cross-encoder (placeholder)"""
        # TODO: Implement cross-encoder reranking when model is available
        # For now, just return top_k based on content quality heuristics
        
        # Sort by content length + authority as proxy for semantic relevance
        scored = []
        for src in sources:
            domain = self.feature_extractor._extract_domain(src.url)
            authority = self.feature_extractor.HIGH_AUTHORITY_DOMAINS.get(domain, 0.3)
            content_score = min(len(src.content) / 3000, 1.0)
            combined_score = authority * 0.6 + content_score * 0.4
            scored.append((combined_score, src))
        
        scored.sort(reverse=True)
        return [src for _, src in scored[:top_k]]
    
    def filter_low_quality(self, sources: List[Dict[str, Any]], threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Quick filter to remove obviously low-quality sources"""
        source_objects = [Source(**s) if isinstance(s, dict) else s for s in sources]
        
        filtered = []
        for src in source_objects:
            domain = self.feature_extractor._extract_domain(src.url)
            authority = self.feature_extractor.HIGH_AUTHORITY_DOMAINS.get(domain, 0.3)
            
            # Skip if very low authority and very short content
            if authority < 0.2 and len(src.content) < 200:
                continue
            
            # Skip if matches low quality patterns
            if self.feature_extractor.low_quality_regex.search(src.title):
                continue
            
            filtered.append(src.to_dict() if hasattr(src, 'to_dict') else src)
        
        return filtered


# Convenience function for quick usage
def rerank_sources(query: str, sources: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
    """Quick rerank function"""
    service = RerankingService()
    return service.rerank(query, sources, top_k=top_k)