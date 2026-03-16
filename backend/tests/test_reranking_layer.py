"""
Tests for Reranking Layer
Run with: pytest backend/tests/test_reranking_layer.py -v
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from reranking_layer import (
    Source, 
    FeatureExtractor, 
    RerankingService,
    rerank_sources
)


class TestSource:
    """Test Source dataclass"""
    
    def test_source_creation(self):
        source = Source(
            title="Test Title",
            url="https://example.com",
            content="Test content here",
            source="Exa",
            score=0.8
        )
        assert source.title == "Test Title"
        assert source.url == "https://example.com"
        assert source.score == 0.8
    
    def test_source_to_dict(self):
        source = Source(
            title="Test",
            url="https://test.com",
            content="Content",
            source="Tavily"
        )
        d = source.to_dict()
        assert d['title'] == "Test"
        assert d['source'] == "Tavily"


class TestFeatureExtractor:
    """Test feature extraction"""
    
    @pytest.fixture
    def extractor(self):
        return FeatureExtractor()
    
    @pytest.fixture
    def sample_source(self):
        return Source(
            title="OpenAI Raises Funding",
            url="https://techcrunch.com/openai-funding",
            content="OpenAI announced a new funding round today. The company plans to expand its AI research.",
            source="Exa"
        )
    
    def test_extract_domain(self, extractor):
        assert extractor._extract_domain("https://www.techcrunch.com/article") == "techcrunch.com"
        assert extractor._extract_domain("http://example.com") == "example.com"
        assert extractor._extract_domain("https://sub.domain.co.uk/path") == "sub.domain.co.uk"
    
    def test_high_authority_domain(self, extractor, sample_source):
        # Change URL to high authority domain
        sample_source.url = "https://www.bloomberg.com/news/article"
        features = extractor.extract_features(sample_source, "OpenAI funding")
        
        # Authority score should be high (index 3)
        assert features[3] == 0.95  # Bloomberg is in HIGH_AUTHORITY_DOMAINS
    
    def test_low_quality_detection(self, extractor):
        low_quality = Source(
            title="Login Page - Sign In",
            url="https://example.com/login",
            content="Please enter your password",
            source="Brave"
        )
        features = extractor.extract_features(low_quality, "test query")
        
        # Quality flags should be 0 (index 7 and 8)
        assert features[7] == 0.0  # Title quality flag
    
    def test_query_relevance(self, extractor, sample_source):
        features = extractor.extract_features(sample_source, "OpenAI funding")
        
        # Title match should be > 0 (index 5)
        assert features[5] > 0.0
        # Content match should be > 0 (index 6)
        assert features[6] > 0.0
    
    def test_content_length_features(self, extractor):
        short_source = Source(
            title="Short",
            url="https://example.com",
            content="Hi",
            source="Exa"
        )
        features = extractor.extract_features(short_source, "test")
        
        # Short content should have low length score (index 0)
        assert features[0] < 0.1
        # Should not have substantial content (index 1)
        assert features[1] == 0.0
    
    def test_freshness_detection(self, extractor):
        fresh_source = Source(
            title="News 2024",
            url="https://example.com",
            content="In 2024, the company announced...",
            source="Tavily"
        )
        features = extractor.extract_features(fresh_source, "test")
        
        # Freshness should be high (index 15)
        assert features[15] == 1.0


class TestRerankingService:
    """Test reranking service"""
    
    @pytest.fixture
    def service(self):
        return RerankingService()
    
    @pytest.fixture
    def sample_sources(self):
        return [
            {
                "title": "OpenAI Funding News",
                "url": "https://techcrunch.com/openai-funding",
                "content": "OpenAI announced a new funding round today...",
                "source": "Exa"
            },
            {
                "title": "OpenAI Wikipedia",
                "url": "https://en.wikipedia.org/wiki/OpenAI",
                "content": "OpenAI is an artificial intelligence research laboratory...",
                "source": "Brave"
            },
            {
                "title": "Random Blog Post",
                "url": "https://random-blog.com/opinion",
                "content": "I think OpenAI is cool...",
                "source": "Brave"
            },
            {
                "title": "Login Page",
                "url": "https://example.com/login",
                "content": "Please sign in to continue...",
                "source": "Tavily"
            }
        ]
    
    def test_rerank_reduces_sources(self, service, sample_sources):
        result = service.rerank(
            query="OpenAI funding",
            sources=sample_sources,
            top_k=3
        )
        
        assert len(result) <= 3
        assert len(result) > 0
    
    def test_rerank_preserves_structure(self, service, sample_sources):
        result = service.rerank(
            query="OpenAI funding",
            sources=sample_sources,
            top_k=2
        )
        
        # Check that required fields are present
        for src in result:
            assert 'title' in src
            assert 'url' in src
            assert 'content' in src
            assert 'source' in src
            assert 'rerank_score' in src
            assert 'rerank_position' in src
    
    def test_high_authority_sources_ranked_higher(self, service):
        sources = [
            {
                "title": "Bloomberg Article",
                "url": "https://www.bloomberg.com/news",
                "content": "Detailed financial analysis...",
                "source": "Exa"
            },
            {
                "title": "Random Blog",
                "url": "https://unknown-blog.com/post",
                "content": "My thoughts on the company...",
                "source": "Brave"
            }
        ]
        
        result = service.rerank(
            query="company analysis",
            sources=sources,
            top_k=2
        )
        
        # Bloomberg should be ranked higher
        assert result[0]['url'] == "https://www.bloomberg.com/news"
    
    def test_filter_low_quality(self, service):
        sources = [
            {
                "title": "Good Article",
                "url": "https://techcrunch.com/article",
                "content": "Detailed content here...",
                "source": "Exa"
            },
            {
                "title": "Login Page",
                "url": "https://example.com/login",
                "content": "Please enter password",
                "source": "Brave"
            },
            {
                "title": "Error 404",
                "url": "https://example.com/not-found",
                "content": "Page not found",
                "source": "Tavily"
            }
        ]
        
        filtered = service.filter_low_quality(sources, threshold=0.3)
        
        # Should filter out login and error pages
        assert len(filtered) == 1
        assert filtered[0]['title'] == "Good Article"
    
    def test_rerank_empty_sources(self, service):
        result = service.rerank("test", [], top_k=5)
        assert result == []
    
    def test_rerank_single_source(self, service):
        sources = [{
            "title": "Only Source",
            "url": "https://example.com",
            "content": "Content here",
            "source": "Exa"
        }]
        
        result = service.rerank("test", sources, top_k=5)
        assert len(result) == 1


class TestIntegration:
    """Integration tests"""
    
    def test_full_pipeline(self):
        """Test the full reranking pipeline"""
        sources = [
            {
                "title": "Crunchbase Profile",
                "url": "https://www.crunchbase.com/organization/openai",
                "content": "OpenAI funding rounds, investors, and financial data...",
                "source": "Exa"
            },
            {
                "title": "LinkedIn Company",
                "url": "https://www.linkedin.com/company/openai",
                "content": "OpenAI company page with employee count and updates...",
                "source": "Tavily"
            },
            {
                "title": "Random Opinion",
                "url": "https://my-blog.com/opinion",
                "content": "I like OpenAI...",
                "source": "Brave"
            },
            {
                "title": "Login Required",
                "url": "https://example.com/login",
                "content": "Sign in to view",
                "source": "Brave"
            }
        ]
        
        # Use convenience function
        result = rerank_sources("OpenAI company funding", sources, top_k=3)
        
        # Should return top 3
        assert len(result) == 3
        
        # Crunchbase and LinkedIn should be in top results
        urls = [r['url'] for r in result]
        assert "https://www.crunchbase.com/organization/openai" in urls
        assert "https://www.linkedin.com/company/openai" in urls
        
        # Login page should be filtered out
        assert "https://example.com/login" not in urls


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_very_long_content(self):
        """Test handling of very long content"""
        service = RerankingService()
        source = {
            "title": "Long Article",
            "url": "https://example.com",
            "content": "Word " * 10000,  # Very long content
            "source": "Exa"
        }
        
        result = service.rerank("test", [source], top_k=1)
        assert len(result) == 1
    
    def test_unicode_content(self):
        """Test handling of unicode characters"""
        service = RerankingService()
        source = {
            "title": "日本語タイトル",
            "url": "https://example.com/日本語",
            "content": "コンテンツです...",
            "source": "Exa"
        }
        
        result = service.rerank("テスト", [source], top_k=1)
        assert len(result) == 1
    
    def test_malformed_urls(self):
        """Test handling of malformed URLs"""
        service = RerankingService()
        sources = [
            {
                "title": "Bad URL",
                "url": "not-a-valid-url",
                "content": "Content",
                "source": "Exa"
            }
        ]
        
        # Should not crash
        result = service.rerank("test", sources, top_k=1)
        assert len(result) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])