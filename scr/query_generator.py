"""
Query Generator - Convert natural language queries to Cypher using Groq
"""

import json
from typing import Dict, List, Optional, Tuple
from loguru import logger
from groq import Groq

from config import Config
from prompt_templates import (
    QUERY_UNDERSTANDING_PROMPT,
    CYPHER_GENERATION_PROMPT
)

class QueryGenerator:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
        
    def understand_query(self, query: str) -> Dict:
        """Parse and understand user's natural language query"""
        logger.info(f"Understanding query: {query}")
        
        prompt = QUERY_UNDERSTANDING_PROMPT.format(query=query)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in warehouse risk management."},
                    {"role": "user", "content": prompt}
                ],
                temperature=Config.LLM_TEMPERATURE,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            understanding = json.loads(response_text)
            logger.info(f"Query intent: {understanding.get('intent')}")
            return understanding
            
        except json.JSONDecodeError:
            logger.error("Failed to parse query understanding")
            return {
                "intent": "general_query",
                "entities": [],
                "risk_factors": [],
                "time_scope": "current",
                "graph_pattern": "simple",
                "complexity": "medium",
                "data_focus": ["warehouses"],
                "output_format": "summary",
                "filters": [],
                "requires_comparison": False,
                "requires_aggregation": False,
                "requires_temporal_analysis": False,
                "requires_geospatial_analysis": False
            }
            
        except Exception as e:
            logger.error(f"Error in query understanding: {e}")
            return {
                "intent": "error", 
                "entities": [], 
                "risk_factors": [],
                "time_scope": "current",
                "graph_pattern": "simple",
                "complexity": "medium",
                "data_focus": ["warehouses"],
                "output_format": "summary",
                "filters": [],
                "requires_comparison": False,
                "requires_aggregation": False,
                "requires_temporal_analysis": False,
                "requires_geospatial_analysis": False
            }

    def generate_cypher(self, query: str, understanding: Dict) -> str:
        """Generate Cypher query from natural language"""
        logger.info("Generating Cypher query...")
        
        prompt = CYPHER_GENERATION_PROMPT.format(
            intent=understanding.get('intent', 'general'),
            query=query,
            entities=understanding.get('entities', []),
            risk_factors=understanding.get('risk_factors', []),
            complexity=understanding.get('complexity', 'medium'),
            graph_pattern=understanding.get('graph_pattern', 'simple'),
            data_focus=understanding.get('data_focus', ['warehouses']),
            time_scope=understanding.get('time_scope', 'current'),
            requires_comparison=understanding.get('requires_comparison', False),
            requires_aggregation=understanding.get('requires_aggregation', False)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Neo4j Cypher query generator for warehouse risk management."},
                    {"role": "user", "content": prompt}
                ],
                temperature=Config.LLM_TEMPERATURE,
                max_tokens=1500
            )
            
            cypher_query = response.choices[0].message.content.strip()
            
            # Clean up the query
            cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
            
            logger.info(f"Generated Cypher:\n{cypher_query}")
            return cypher_query
            
        except Exception as e:
            logger.error(f"Error generating Cypher: {e}")
            return ""

    def get_template_query(self, intent: str, entities: List[str]) -> Optional[str]:
        """Get pre-defined Cypher template for common queries"""
        
        templates = {
            "high_risk_warehouses": """
                MATCH (w:Warehouse)-[:EXPERIENCED]->(r:RiskEvent)
                WHERE w.risk_score > 0.6
                OPTIONAL MATCH (w)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
                OPTIONAL MATCH (w)-[:OPERATES_IN]->(m:MarketContext)
                WITH w, COUNT(r) as risk_count, i, m
                RETURN w.warehouse_id as warehouse_id,
                       w.risk_score as risk_score,
                       w.location_type as location,
                       risk_count,
                       i.has_electric_backup as has_backup,
                       i.is_flood_proof as flood_proof,
                       m.is_flood_impacted as in_flood_zone
                ORDER BY w.risk_score DESC
                LIMIT 10
            """,
            
            "warehouse_risk_profile": """
                MATCH (w:Warehouse {warehouse_id: $warehouse_id})
                OPTIONAL MATCH (w)-[e:EXPERIENCED]->(r:RiskEvent)
                OPTIONAL MATCH (w)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
                OPTIONAL MATCH (w)-[:OPERATES_IN]->(m:MarketContext)
                OPTIONAL MATCH (w)-[:LOCATED_IN]->(rz:RegionalZone)-[:PART_OF]->(z:Zone)
                RETURN w, 
                       collect(DISTINCT {type: r.event_type, count: r.occurrence_count, severity: r.severity}) as risks,
                       i,
                       m,
                       rz.regional_zone_name as region,
                       z.zone_name as zone
            """,
            
            "zone_risk_comparison": """
                MATCH (z:Zone)<-[:PART_OF]-(rz:RegionalZone)<-[:LOCATED_IN]-(w:Warehouse)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH z.zone_name as zone,
                     COUNT(DISTINCT w) as total_warehouses,
                     AVG(w.risk_score) as avg_risk_score,
                     COUNT(r) as total_incidents
                RETURN zone, 
                       total_warehouses,
                       ROUND(avg_risk_score, 3) as avg_risk_score,
                       total_incidents,
                       ROUND(total_incidents * 1.0 / total_warehouses, 2) as incident_rate
                ORDER BY avg_risk_score DESC
            """,
            
            "infrastructure_impact": """
                MATCH (w:Warehouse)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH i.has_temp_regulation as has_temp_reg,
                     i.has_electric_backup as has_backup,
                     i.is_flood_proof as flood_proof,
                     COUNT(DISTINCT w) as warehouse_count,
                     AVG(w.risk_score) as avg_risk,
                     COUNT(r) as total_incidents
                RETURN has_temp_reg, has_backup, flood_proof,
                       warehouse_count,
                       ROUND(avg_risk, 3) as avg_risk_score,
                       total_incidents
                ORDER BY avg_risk_score
            """,
            
            "manager_performance": """
                MATCH (m:Manager)-[:MANAGES]->(w:Warehouse)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH m.manager_id as manager_id,
                     COUNT(DISTINCT w) as warehouses_managed,
                     AVG(w.risk_score) as avg_risk_score,
                     AVG(w.product_shipped_tons) as avg_shipment,
                     COUNT(r) as total_incidents
                WHERE warehouses_managed > 0
                RETURN manager_id,
                       warehouses_managed,
                       ROUND(avg_risk_score, 3) as avg_risk_score,
                       ROUND(avg_shipment, 2) as avg_shipment_tons,
                       total_incidents,
                       ROUND(total_incidents * 1.0 / warehouses_managed, 2) as incidents_per_warehouse
                ORDER BY avg_risk_score ASC, avg_shipment DESC
                LIMIT 15
            """,
            
            "vulnerable_warehouses": """
                MATCH (w:Warehouse)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
                WHERE i.has_electric_backup = false
                  OR i.is_flood_proof = false
                OPTIONAL MATCH (w)-[:OPERATES_IN]->(m:MarketContext)
                WHERE m.is_flood_impacted = true
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH w, i, m, COUNT(r) as incident_count
                WHERE w.risk_score > 0.5 OR incident_count > 2
                RETURN w.warehouse_id as warehouse_id,
                       w.risk_score as risk_score,
                       w.location_type as location,
                       i.has_electric_backup as has_backup,
                       i.is_flood_proof as flood_proof,
                       m.is_flood_impacted as in_flood_zone,
                       incident_count
                ORDER BY w.risk_score DESC, incident_count DESC
                LIMIT 10
            """,
            
            "breakdown_patterns": """
                MATCH (w:Warehouse)-[:EXPERIENCED]->(r:RiskEvent)
                WHERE r.event_type = 'breakdown'
                OPTIONAL MATCH (w)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
                OPTIONAL MATCH (w)-[:LOCATED_IN]->(rz:RegionalZone)
                WITH w, r, i, rz
                RETURN w.warehouse_id as warehouse_id,
                       w.established_year as year_established,
                       r.occurrence_count as breakdown_count,
                       r.severity as severity,
                       i.has_electric_backup as has_backup,
                       i.has_temp_regulation as has_temp_control,
                       rz.regional_zone_name as region
                ORDER BY r.occurrence_count DESC
                LIMIT 15
            """,
            
            "exploration": """
                MATCH (w:Warehouse)
                OPTIONAL MATCH (w)-[:LOCATED_IN]->(rz:RegionalZone)-[:PART_OF]->(z:Zone)
                OPTIONAL MATCH (w)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                RETURN w.warehouse_id,
                       w.location_type,
                       w.capacity_size,
                       z.zone_name,
                       rz.regional_zone_name,
                       w.risk_score,
                       COUNT(r) as risk_events,
                       i.has_temp_regulation,
                       i.has_electric_backup,
                       i.is_flood_proof
                ORDER BY w.warehouse_id
                LIMIT 50
            """,
            
            "capacity_analysis": """
                MATCH (w:Warehouse)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH w, COUNT(r) as incident_count
                RETURN w.capacity_size,
                       COUNT(w) as warehouse_count,
                       AVG(w.risk_score) as avg_risk,
                       AVG(w.product_shipped_tons) as avg_shipment,
                       SUM(incident_count) as total_incidents,
                       AVG(incident_count) as avg_incidents_per_warehouse
                ORDER BY w.capacity_size
            """,
            
            "infrastructure_gaps": """
                MATCH (w:Warehouse)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
                WHERE i.has_electric_backup = false 
                   OR i.is_flood_proof = false 
                   OR i.has_temp_regulation = false
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                RETURN w.warehouse_id,
                       w.risk_score,
                       i.has_temp_regulation,
                       i.has_electric_backup,
                       i.is_flood_proof,
                       COUNT(r) as risk_events,
                       CASE 
                         WHEN i.has_electric_backup = false AND i.is_flood_proof = false THEN 'Critical'
                         WHEN i.has_electric_backup = false OR i.is_flood_proof = false THEN 'High'
                         ELSE 'Medium'
                       END as vulnerability_level
                ORDER BY w.risk_score DESC
                LIMIT 20
            """,
            
            "market_risk_correlation": """
                MATCH (w:Warehouse)-[:OPERATES_IN]->(m:MarketContext)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH m, COUNT(DISTINCT w) as warehouses_in_market,
                     AVG(w.risk_score) as avg_warehouse_risk,
                     COUNT(r) as total_market_risk_events,
                     SUM(m.competitor_count) as total_competitors,
                     SUM(m.retail_shop_count) as total_retail_shops
                RETURN m.market_id,
                       warehouses_in_market,
                       ROUND(avg_warehouse_risk, 3) as avg_risk_score,
                       total_market_risk_events,
                       ROUND(total_market_risk_events * 1.0 / warehouses_in_market, 2) as risk_per_warehouse,
                       total_competitors,
                       total_retail_shops,
                       m.is_flood_impacted
                ORDER BY avg_warehouse_risk DESC
            """,
            
            "performance_metrics": """
                MATCH (w:Warehouse)
                OPTIONAL MATCH (w)-[:MANAGES]->(mgr:Manager)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH mgr, COUNT(DISTINCT w) as warehouses_managed,
                     AVG(w.risk_score) as avg_risk,
                     AVG(w.product_shipped_tons) as avg_shipments,
                     COUNT(r) as total_risk_events
                WHERE warehouses_managed > 0
                RETURN mgr.manager_id,
                       warehouses_managed,
                       ROUND(avg_risk, 3) as avg_warehouse_risk,
                       ROUND(avg_shipments, 2) as avg_shipments_per_warehouse,
                       total_risk_events,
                       ROUND(total_risk_events * 1.0 / warehouses_managed, 2) as risk_events_per_warehouse
                ORDER BY avg_risk ASC, avg_shipments DESC
            """,
            
            "location_risk_analysis": """
                MATCH (w:Warehouse)-[:LOCATED_IN]->(rz:RegionalZone)-[:PART_OF]->(z:Zone)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH z.zone_name as zone, rz.regional_zone_name as region,
                     COUNT(DISTINCT w) as warehouses_in_region,
                     AVG(w.risk_score) as avg_risk,
                     COUNT(r) as total_incidents,
                     SUM(CASE WHEN w.location_type = 'Urban' THEN 1 ELSE 0 END) as urban_count,
                     SUM(CASE WHEN w.location_type = 'Rural' THEN 1 ELSE 0 END) as rural_count
                RETURN zone,
                       region,
                       warehouses_in_region,
                       ROUND(avg_risk, 3) as avg_risk_score,
                       total_incidents,
                       ROUND(total_incidents * 1.0 / warehouses_in_region, 2) as incidents_per_warehouse,
                       urban_count,
                       rural_count
                ORDER BY avg_risk DESC
            """,
            
            "temporal_risk_trends": """
                MATCH (w:Warehouse)-[:EXPERIENCED]->(r:RiskEvent)
                WHERE r.time_period = 'l3m'
                WITH r.event_type as event_type,
                     COUNT(r) as recent_events,
                     AVG(r.severity) as avg_severity,
                     COUNT(DISTINCT w) as affected_warehouses
                RETURN event_type,
                       recent_events,
                       ROUND(avg_severity, 2) as avg_severity,
                       affected_warehouses,
                       ROUND(recent_events * 1.0 / affected_warehouses, 2) as events_per_affected_warehouse
                ORDER BY recent_events DESC
                LIMIT 10
            """,
            
            "compliance_overview": """
                MATCH (w:Warehouse)-[:SUBJECT_TO]->(c:Compliance)
                OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
                WITH c, COUNT(DISTINCT w) as warehouses_under_compliance,
                     AVG(w.risk_score) as avg_risk_under_compliance,
                     COUNT(r) as total_risk_events,
                     AVG(c.govt_checks_l3m) as avg_govt_checks,
                     AVG(c.refill_requests_l3m) as avg_refill_requests
                RETURN c.certificate_type,
                       warehouses_under_compliance,
                       ROUND(avg_risk_under_compliance, 3) as avg_risk_score,
                       total_risk_events,
                       ROUND(avg_govt_checks, 1) as avg_govt_checks_per_warehouse,
                       ROUND(avg_refill_requests, 1) as avg_refill_requests_per_warehouse
                ORDER BY avg_risk_under_compliance DESC
            """
        }
        
        return templates.get(intent)

    def process_query(self, query: str, use_templates: bool = True) -> Tuple[str, Dict]:
        """Complete query processing pipeline"""
        understanding = self.understand_query(query)
        
        # Ensure understanding has all required fields with defaults
        understanding.setdefault('complexity', 'medium')
        understanding.setdefault('graph_pattern', 'simple')
        understanding.setdefault('data_focus', ['warehouses'])
        understanding.setdefault('time_scope', 'current')
        understanding.setdefault('requires_comparison', False)
        understanding.setdefault('requires_aggregation', False)
        understanding.setdefault('requires_temporal_analysis', False)
        understanding.setdefault('requires_geospatial_analysis', False)
        understanding.setdefault('output_format', 'summary')
        understanding.setdefault('filters', [])
        
        if use_templates:
            intent = understanding.get('intent', '')
            template = self.get_template_query(intent, understanding.get('entities', []))
            if template:
                logger.info(f"Using template for intent: {intent}")
                return template.strip(), understanding
        
        # Try to generate custom Cypher
        cypher_query = self.generate_cypher(query, understanding)
        
        # Validate the generated query
        if cypher_query and self._validate_cypher_syntax(cypher_query):
            return cypher_query, understanding
        else:
            # Fallback to a basic exploration query
            logger.warning("Generated query failed validation, using fallback")
            fallback_query = self._generate_fallback_query(understanding)
            return fallback_query, understanding
    
    def _validate_cypher_syntax(self, cypher_query: str) -> bool:
        """Basic validation of Cypher query syntax"""
        try:
            # Check for basic syntax issues
            if not cypher_query.strip():
                return False
            if not cypher_query.upper().startswith(('MATCH', 'CREATE', 'MERGE')):
                return False
            if 'RETURN' not in cypher_query.upper():
                return False
            return True
        except Exception:
            return False
    
    def _generate_fallback_query(self, understanding: Dict) -> str:
        """Generate a safe fallback query based on understanding"""
        intent = understanding.get('intent', 'exploration')
        entities = understanding.get('entities', [])
        
        if intent == 'risk_identification':
            return """
            MATCH (w:Warehouse)
            WHERE w.risk_score > 0.5
            OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
            RETURN w.warehouse_id, w.risk_score, w.location_type, COUNT(r) as risk_events
            ORDER BY w.risk_score DESC
            LIMIT 10
            """
        elif 'warehouse' in entities or any('WH_' in str(e) for e in entities):
            warehouse_id = next((e for e in entities if 'WH_' in str(e)), 'WH_0001')
            return f"""
            MATCH (w:Warehouse {{warehouse_id: '{warehouse_id}'}})
            OPTIONAL MATCH (w)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
            OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
            RETURN w.warehouse_id, w.risk_score, w.location_type,
                   i.has_temp_regulation, i.has_electric_backup, i.is_flood_proof,
                   COUNT(r) as risk_events
            """
        else:
            return """
            MATCH (w:Warehouse)
            OPTIONAL MATCH (w)-[:LOCATED_IN]->(rz:RegionalZone)-[:PART_OF]->(z:Zone)
            RETURN w.warehouse_id, w.location_type, w.capacity_size, z.zone_name, w.risk_score
            ORDER BY w.risk_score DESC
            LIMIT 20
            """

if __name__ == "__main__":
    generator = QueryGenerator()
    test_queries = [
        # Risk Analysis
        "Show me the top 10 high-risk warehouses",
        "Which warehouses have infrastructure vulnerabilities?",
        "Find warehouses with flood risk but no flood protection",
        
        # Performance Analysis
        "How are managers performing based on warehouse risk?",
        "Compare capacity utilization across different warehouse sizes",
        "Show me shipment volumes by location type",
        
        # Geographic Analysis
        "Which zones have the highest risk scores?",
        "Compare urban vs rural warehouse performance",
        "Show regional risk distribution",
        
        # Market Analysis
        "How does market competition affect warehouse risk?",
        "Find warehouses in flood-impacted markets",
        "Analyze risk patterns by competitor density",
        
        # Compliance & Infrastructure
        "Which warehouses need better compliance monitoring?",
        "Show infrastructure gaps across the network",
        "Find warehouses without temperature regulation",
        
        # Specific Warehouse Queries
        "What's the risk profile of warehouse WH_0001?",
        "Show me all details for warehouse WH_0100",
        "Give me a complete analysis of warehouse WH_0050",
        
        # Temporal Analysis
        "What are the most common risk events in the last 3 months?",
        "Show risk trends over time",
        "Compare current vs historical performance",
        
        # Complex Analysis
        "Find correlations between market factors and warehouse risk",
        "Identify warehouses that are both high-risk and high-performing",
        "Show me warehouses that are underperforming despite good infrastructure",
        
        # General Exploration
        "Give me an overview of all warehouses",
        "Show me the complete network structure",
        "List all warehouse locations and their characteristics"
    ]

    print(f"Testing {len(test_queries)} different query types...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {query}")
        print(f"{'='*80}")
        
        try:
            cypher, understanding = generator.process_query(query)
            print(f"Intent: {understanding.get('intent', 'unknown')}")
            print(f"Entities: {understanding.get('entities', [])}")
            print(f"Cypher Query:\n{cypher}")
        except Exception as e:
            print(f"Error processing query: {e}")