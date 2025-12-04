"""
Query Executor - Execute Cypher queries and process results
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from loguru import logger
import pandas as pd

from config import Config

class QueryExecutor:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
        )
        self.database = Config.NEO4J_DATABASE
    
    def close(self):
        self.driver.close()
    
    def execute_query(
        self, 
        cypher_query: str, 
        parameters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Execute Cypher query and return results"""
        logger.info("Executing query...")
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher_query, parameters or {})
                records = [dict(record) for record in result]
                
                logger.info(f"Query returned {len(records)} results")
                return records
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {cypher_query}")
            return []
    
    def execute_with_context(
        self, 
        cypher_query: str, 
        parameters: Optional[Dict] = None,
        max_hops: int = 3
    ) -> Dict[str, Any]:
        """Execute query and gather contextual information"""
        primary_results = self.execute_query(cypher_query, parameters)
        
        if not primary_results:
            return {
                "results": [],
                "context": {},
                "summary": "No results found"
            }
        
        # Extract warehouse IDs for context
        warehouse_ids = []
        for record in primary_results:
            if 'warehouse_id' in record:
                warehouse_ids.append(record['warehouse_id'])
        
        # Gather additional context
        context = {}
        if warehouse_ids:
            context['related_entities'] = self._get_related_entities(warehouse_ids[:5])
            context['risk_summary'] = self._get_risk_summary(warehouse_ids[:5])
        
        return {
            "results": primary_results,
            "context": context,
            "summary": self._generate_results_summary(primary_results)
        }
    
    def _get_related_entities(self, warehouse_ids: List[str]) -> Dict:
        """Get related entities for context"""
        query = """
        MATCH (w:Warehouse)
        WHERE w.warehouse_id IN $warehouse_ids
        OPTIONAL MATCH (w)-[:LOCATED_IN]->(rz:RegionalZone)-[:PART_OF]->(z:Zone)
        OPTIONAL MATCH (w)-[:OPERATES_IN]->(m:MarketContext)
        RETURN w.warehouse_id as warehouse_id,
               rz.regional_zone_name as region,
               z.zone_name as zone,
               m.competitor_count as competitors,
               m.retail_shop_count as retail_shops
        """
        
        return self.execute_query(query, {"warehouse_ids": warehouse_ids})
    
    def _get_risk_summary(self, warehouse_ids: List[str]) -> Dict:
        """Get risk event summary"""
        query = """
        MATCH (w:Warehouse)-[:EXPERIENCED]->(r:RiskEvent)
        WHERE w.warehouse_id IN $warehouse_ids
        RETURN w.warehouse_id as warehouse_id,
               r.event_type as event_type,
               SUM(r.occurrence_count) as total_occurrences
        ORDER BY total_occurrences DESC
        """
        
        results = self.execute_query(query, {"warehouse_ids": warehouse_ids})
        
        summary = {}
        for record in results:
            event_type = record['event_type']
            if event_type not in summary:
                summary[event_type] = 0
            summary[event_type] += record['total_occurrences']
        
        return summary
    
    def _generate_results_summary(self, results: List[Dict]) -> str:
        """Generate human-readable summary"""
        if not results:
            return "No results found"
        
        count = len(results)
        
        if 'risk_score' in results[0]:
            avg_risk = sum(r.get('risk_score', 0) for r in results) / count
            return f"Found {count} warehouses with average risk score {avg_risk:.3f}"
        
        elif 'zone' in results[0]:
            zones = set(r['zone'] for r in results if 'zone' in r)
            return f"Analysis across {len(zones)} zones with {count} data points"
        
        else:
            return f"Query returned {count} results"
    
    def results_to_dataframe(self, results: List[Dict]) -> pd.DataFrame:
        """Convert results to pandas DataFrame"""
        if not results:
            return pd.DataFrame()
        
        return pd.DataFrame(results)
    
    def validate_query(self, cypher_query: str) -> bool:
        """Validate Cypher query syntax"""
        try:
            with self.driver.session(database=self.database) as session:
                session.run("EXPLAIN " + cypher_query)
            return True
        except Exception as e:
            logger.error(f"Query validation failed: {e}")
            return False

if __name__ == "__main__":
    executor = QueryExecutor()
    
    cypher = """
    MATCH (w:Warehouse)
    WHERE w.risk_score > 0.6
    RETURN w.warehouse_id, w.risk_score, w.location_type
    ORDER BY w.risk_score DESC
    LIMIT 5
    """
    
    try:
        results = executor.execute_with_context(cypher)
        
        print("\n📊 Results:")
        for record in results['results']:
            print(record)
        
        print("\n🔍 Context:")
        print(results['context'])
        
    finally:
        executor.close()


