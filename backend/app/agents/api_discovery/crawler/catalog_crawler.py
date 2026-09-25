import hashlib
import logging
import os
from typing import Dict, List, Optional
from app.agents.api_discovery.events import event_stream
from app.agents.api_discovery.models import EndpointMetadataModel
from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser

logger = logging.getLogger("agentflow.api_discovery.crawler")


class CatalogCrawler:
    """Enterprise Catalog Crawler & Incremental Indexer featuring Delta Update Checksums and Hot Reload."""

    def __init__(self) -> None:
        self.parser = EnterpriseSpecParser()
        self._checksum_cache: Dict[str, str] = {}

    def compute_checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def crawl_and_index_file(self, file_path: str) -> Optional[List[EndpointMetadataModel]]:
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        checksum = self.compute_checksum(content)
        # Check if modified
        if self._checksum_cache.get(file_path) == checksum:
            logger.debug(f"Catalog file '{file_path}' unchanged. Skipping re-indexing.")
            return None

        parsed = self.parser.parse_spec(content)
        self._checksum_cache[file_path] = checksum

        event_stream.publish("CatalogUpdated", {"file_path": file_path, "indexed_count": len(parsed)})
        logger.info(f"Incremental Indexer re-indexed catalog file '{file_path}': {len(parsed)} endpoints.")
        return parsed


catalog_crawler = CatalogCrawler()
