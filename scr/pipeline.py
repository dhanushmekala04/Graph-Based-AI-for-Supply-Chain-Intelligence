"""
12. SRC/PIPELINE.PY - Complete GraphRAG Pipeline
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
from time import time
from config import Config
from ingestion import DataIngestion
from graph_bulider import GraphBuilder
from query_generator import QueryGenerator
from answer_generator import AnswerGenerator
from executor import QueryExecutor

class GraphRAGPipeline:
    """End-to-end GraphRAG pipeline for warehouse risk analysis"""
    
    def __init__(self):
        logger.info("Initializing GraphRAG Pipeline...")
        self.query_generator = QueryGenerator()
        self.executor = QueryExecutor()
        self.answer_generator = AnswerGenerator()
        logger.info("✅ Pipeline initialized")
    
    def process_query(
        self, 
        user_query: str,
        use_templates: bool = True,
        generate_recommendations: bool = False
    ) -> Dict[str, Any]:
        """
        Complete query processing pipeline
        
        Args:
            user_query: Natural language query
            use_templates: Use predefined templates when available
            generate_recommendations: Generate actionable recommendations
        
        Returns:
            Dictionary containing answer, results, metadata
        """
        start_time = time()
        logger.info(f"\n{'='*60}\nProcessing query: {user_query}\n{'='*60}")
        
        try:
            # Step 1: Generate Cypher query
            logger.info("Step 1: Generating Cypher query...")
            cypher_query, understanding = self.query_generator.process_query(
                user_query, 
                use_templates=use_templates
            )
            
            if not cypher_query:
                return self._error_response("Failed to generate valid query")
            
            # Step 2: Execute query
            logger.info("Step 2: Executing graph query...")
            execution_result = self.executor.execute_with_context(cypher_query)
            
            results = execution_result.get('results', [])
            context = execution_result.get('context', {})
            
            if not results:
                return self._no_results_response(user_query, understanding)
            
            # Step 3: Generate answer
            logger.info("Step 3: Generating answer...")
            answer = self.answer_generator.generate_answer(
                user_query,
                results,
                context,
                understanding
            )
            
            # Step 4: Optional recommendations
            recommendations = None
            if generate_recommendations and understanding.get('intent') == 'risk_identification':
                logger.info("Step 4: Generating recommendations...")
                recommendations = self._generate_warehouse_recommendations(results)
            
            processing_time = time() - start_time
            
            response = {
                "success": True,
                "query": user_query,
                "answer": answer,
                "results": results[:Config.MAX_RESULTS],
                "result_count": len(results),
                "context": context,
                "understanding": understanding,
                "cypher_query": cypher_query,
                "recommendations": recommendations,
                "metadata": {
                    "processing_time_seconds": round(processing_time, 2),
                    "results_returned": len(results),
                    "query_complexity": understanding.get('complexity', 'unknown'),
                    "graph_pattern": understanding.get('graph_pattern', 'unknown')
                }
            }
            
            logger.info(f"✅ Query processed in {processing_time:.2f} seconds")
            return response
            
        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}", exc_info=True)
            return self._error_response(str(e))
    
    def batch_process(
        self, 
        queries: List[str]
    ) -> List[Dict[str, Any]]:
        """Process multiple queries in batch"""
        logger.info(f"Processing {len(queries)} queries in batch...")
        results = []
        
        for i, query in enumerate(queries, 1):
            logger.info(f"\nProcessing query {i}/{len(queries)}")
            result = self.process_query(query)
            results.append(result)
        
        logger.info(f"✅ Batch processing completed: {len(results)} queries processed")
        return results
    
    def get_warehouse_profile(
        self, 
        warehouse_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive warehouse profile with risk assessment"""
        logger.info(f"Generating profile for warehouse: {warehouse_id}")
        
        # Query warehouse data
        cypher = """
        MATCH (w:Warehouse {warehouse_id: $warehouse_id})
        OPTIONAL MATCH (w)-[e:EXPERIENCED]->(r:RiskEvent)
        OPTIONAL MATCH (w)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
        OPTIONAL MATCH (w)-[:OPERATES_IN]->(m:MarketContext)
        OPTIONAL MATCH (w)-[:LOCATED_IN]->(rz:RegionalZone)-[:PART_OF]->(z:Zone)
        OPTIONAL MATCH (w)-[:SUBJECT_TO]->(c:Compliance)
        OPTIONAL MATCH (mgr:Manager)-[:MANAGES]->(w)
        RETURN w, 
               collect(DISTINCT {
                   type: r.event_type, 
                   count: r.occurrence_count, 
                   severity: r.severity
               }) as risks,
               i as infrastructure,
               m as market,
               rz.regional_zone_name as region,
               z.zone_name as zone,
               c as compliance,
               mgr.manager_id as manager_id
        """
        
        results = self.executor.execute_query(cypher, {"warehouse_id": warehouse_id})
        
        if not results:
            return {"error": f"Warehouse {warehouse_id} not found"}
        
        warehouse_data = results[0]
        
        # Generate risk assessment
        risk_assessment = self.answer_generator.generate_risk_assessment(
            warehouse_id,
            warehouse_data
        )
        
        # Get similar warehouses for benchmarking
        similar_warehouses = self._find_similar_warehouses(warehouse_data)
        
        # Generate recommendations
        recommendations = self.answer_generator.generate_recommendations(
            warehouse_data,
            similar_warehouses
        )
        
        return {
            "warehouse_id": warehouse_id,
            "data": warehouse_data,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "similar_warehouses": similar_warehouses[:5]
        }
    
    def compare_warehouses(
        self, 
        warehouse_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple warehouses across metrics"""
        logger.info(f"Comparing {len(warehouse_ids)} warehouses")
        
        if metrics is None:
            metrics = ["risk_score", "incidents", "infrastructure", "performance"]
        
        # Query warehouse data
        cypher = """
        MATCH (w:Warehouse)
        WHERE w.warehouse_id IN $warehouse_ids
        OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
        OPTIONAL MATCH (w)-[:HAS_INFRASTRUCTURE]->(i:Infrastructure)
        WITH w, 
             COUNT(r) as incident_count,
             collect(DISTINCT r.event_type) as incident_types,
             i
        RETURN w.warehouse_id as warehouse_id,
               w.risk_score as risk_score,
               w.product_shipped_tons as shipped_tons,
               w.location_type as location,
               incident_count,
               incident_types,
               i.has_electric_backup as has_backup,
               i.is_flood_proof as flood_proof
        """
        
        warehouses = self.executor.execute_query(cypher, {"warehouse_ids": warehouse_ids})
        
        if not warehouses:
            return {"error": "No warehouses found"}
        
        # Generate comparison
        comparison = self.answer_generator.generate_comparison(warehouses, metrics)
        
        return {
            "warehouses": warehouses,
            "comparison": comparison,
            "metrics_compared": metrics
        }
    
    def _find_similar_warehouses(
        self, 
        warehouse_data: Dict, 
        limit: int = 5
    ) -> List[Dict]:
        """Find similar warehouses for benchmarking"""
        cypher = """
        MATCH (w:Warehouse)
        WHERE w.warehouse_id <> $warehouse_id
          AND w.location_type = $location_type
          AND abs(w.risk_score - $risk_score) < 0.2
        OPTIONAL MATCH (w)-[:EXPERIENCED]->(r:RiskEvent)
        WITH w, COUNT(r) as incident_count
        RETURN w.warehouse_id as warehouse_id,
               w.risk_score as risk_score,
               w.product_shipped_tons as shipped_tons,
               incident_count
        ORDER BY abs(w.risk_score - $risk_score)
        LIMIT $limit
        """
        
        params = {
            "warehouse_id": warehouse_data.get('w', {}).get('warehouse_id'),
            "location_type": warehouse_data.get('w', {}).get('location_type'),
            "risk_score": warehouse_data.get('w', {}).get('risk_score', 0.5),
            "limit": limit
        }
        
        return self.executor.execute_query(cypher, params)
    
    def _generate_warehouse_recommendations(
        self, 
        results: List[Dict]
    ) -> List[Dict]:
        """Generate recommendations for high-risk warehouses"""
        recommendations = []
        
        for record in results[:3]:  # Top 3 high-risk warehouses
            warehouse_id = record.get('warehouse_id')
            if warehouse_id:
                rec = {
                    "warehouse_id": warehouse_id,
                    "priority": self._calculate_priority(record),
                    "actions": self._suggest_actions(record)
                }
                recommendations.append(rec)
        
        return recommendations
    
    def _calculate_priority(self, record: Dict) -> str:
        """Calculate intervention priority"""
        risk_score = record.get('risk_score', 0)
        incident_count = record.get('risk_count', 0) or record.get('incident_count', 0)
        
        if risk_score > 0.75 or incident_count > 3:
            return "CRITICAL"
        elif risk_score > 0.6 or incident_count > 2:
            return "HIGH"
        elif risk_score > 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _suggest_actions(self, record: Dict) -> List[str]:
        """Suggest specific actions based on warehouse data"""
        actions = []
        
        risk_score = record.get('risk_score', 0)
        has_backup = record.get('has_backup', True)
        flood_proof = record.get('flood_proof', True)
        in_flood_zone = record.get('in_flood_zone', False)
        
        if risk_score > 0.7:
            actions.append("Immediate risk assessment required")
        
        if not has_backup:
            actions.append("Install electric backup system")
        
        if not flood_proof and in_flood_zone:
            actions.append("Implement flood protection measures")
        
        if record.get('incident_count', 0) > 2:
            actions.append("Investigate recurring incident patterns")
        
        if not actions:
            actions.append("Continue monitoring")
        
        return actions
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "success": False,
            "error": error_message,
            "answer": f"I encountered an error processing your query: {error_message}",
            "results": [],
            "result_count": 0,
            "metadata": {
                "processing_time_seconds": 0.0,
                "results_returned": 0,
                "query_complexity": "error",
                "graph_pattern": "error"
            }
        }
    
    def _no_results_response(
        self, 
        query: str, 
        understanding: Dict
    ) -> Dict[str, Any]:
        """Generate response when no results found"""
        return {
            "success": True,
            "query": query,
            "answer": "No warehouses match your query criteria. Try broadening your search or adjusting the filters.",
            "results": [],
            "result_count": 0,
            "understanding": understanding,
            "suggestion": "Try queries like: 'Show all warehouses' or 'List warehouses by zone'",
            "metadata": {
                "processing_time_seconds": 0.0,
                "results_returned": 0,
                "query_complexity": understanding.get('complexity', 'unknown'),
                "graph_pattern": understanding.get('graph_pattern', 'unknown')
            }
        }
    
    def close(self):
        """Close database connections"""
        self.executor.close()
        logger.info("Pipeline closed")

