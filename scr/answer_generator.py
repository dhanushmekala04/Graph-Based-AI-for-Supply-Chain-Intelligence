"""
Answer Generator - Generate natural language answers from Cypher results
"""

import json
from typing import Dict, List, Optional, Any
from loguru import logger
from groq import Groq

from config import Config
from prompt_templates import (
    QUERY_UNDERSTANDING_PROMPT,
    CYPHER_GENERATION_PROMPT,
    CONTEXT_EXTRACTION_PROMPT,
    ANSWER_GENERATION_PROMPT,
    RISK_ASSESSMENT_PROMPT,
    RECOMMENDATION_PROMPT,
    COMPARISON_PROMPT
)

class AnswerGenerator:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
        self.max_tokens = Config.LLM_MAX_TOKENS
        self.temperature = Config.LLM_TEMPERATURE
    
    def extract_context(self, query: str, results: List[Dict]) -> str:
        """Extract relevant context from query results"""
        if not results:
            return "No data found in the knowledge graph."
        
        results_text = json.dumps(results, indent=2, default=str)
        
        prompt = CONTEXT_EXTRACTION_PROMPT.format(
            query=query,
            results=results_text[:3000]
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error extracting context: {e}")
            return "Error extracting context"
    
    def generate_answer(
        self, 
        query: str, 
        results: List[Dict],
        context: Dict[str, Any],
        understanding: Dict
    ) -> str:
        """Generate comprehensive answer from query results"""
        logger.info("Generating answer...")
        
        context_summary = self.extract_context(query, results)
        results_summary = self._format_results_summary(results, understanding)
        
        prompt = ANSWER_GENERATION_PROMPT.format(
            query=query,
            context=json.dumps(context, indent=2, default=str)[:2000],
            results_summary=results_summary
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a warehouse risk assessment analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content
            logger.info("Answer generated successfully")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Error generating answer. Please try again."
    
    def generate_risk_assessment(
        self, 
        warehouse_id: str, 
        warehouse_data: Dict
    ) -> str:
        """Generate detailed risk assessment"""
        logger.info(f"Generating risk assessment for {warehouse_id}")
        
        prompt = RISK_ASSESSMENT_PROMPT.format(
            warehouse_id=warehouse_id,
            risk_score=warehouse_data.get('risk_score', 'N/A'),
            incidents=json.dumps(warehouse_data.get('risks', []), indent=2),
            infrastructure=json.dumps(warehouse_data.get('infrastructure', {}), indent=2),
            market=json.dumps(warehouse_data.get('market', {}), indent=2)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a risk assessment expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating risk assessment: {e}")
            return "Error generating risk assessment"
    
    def generate_recommendations(
        self, 
        warehouse_data: Dict,
        similar_warehouses: List[Dict]
    ) -> str:
        """Generate actionable recommendations"""
        logger.info("Generating recommendations...")
        
        issues = self._identify_issues(warehouse_data)
        
        prompt = RECOMMENDATION_PROMPT.format(
            current_state=json.dumps(warehouse_data, indent=2, default=str),
            issues=json.dumps(issues, indent=2),
            benchmarks=json.dumps(similar_warehouses[:3], indent=2, default=str)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a business consultant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return "Error generating recommendations"
    
    def generate_comparison(
        self, 
        warehouses: List[Dict],
        metrics: List[str]
    ) -> str:
        """Generate comparative analysis"""
        logger.info(f"Generating comparison for {len(warehouses)} warehouses")
        
        prompt = COMPARISON_PROMPT.format(
            warehouses=json.dumps(warehouses, indent=2, default=str),
            metrics=json.dumps(metrics, indent=2)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a comparative analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating comparison: {e}")
            return "Error generating comparison"
    
    def _format_results_summary(
        self, 
        results: List[Dict],
        understanding: Dict
    ) -> str:
        """Format results into readable summary"""
        if not results:
            return "No results found."
        
        intent = understanding.get('intent', 'general')
        
        if intent == 'risk_identification':
            return self._format_risk_results(results)
        elif intent == 'comparison':
            return self._format_comparison_results(results)
        else:
            return json.dumps(results[:10], indent=2, default=str)
    
    def _format_risk_results(self, results: List[Dict]) -> str:
        """Format risk-focused results"""
        summary = []
        summary.append(f"Found {len(results)} warehouses with risk indicators:\n")
        
        for i, record in enumerate(results[:10], 1):
            wh_id = record.get('warehouse_id', 'Unknown')
            risk_score = record.get('risk_score', 0)
            incidents = record.get('risk_count', 0) or record.get('incident_count', 0)
            
            summary.append(
                f"{i}. {wh_id}: Risk Score={risk_score:.3f}, Incidents={incidents}"
            )
        
        return "\n".join(summary)
    
    def _format_comparison_results(self, results: List[Dict]) -> str:
        """Format comparison results"""
        summary = []
        summary.append("Comparison Results:\n")
        
        for record in results:
            if 'zone' in record:
                summary.append(
                    f"- {record['zone']}: "
                    f"Avg Risk={record.get('avg_risk_score', 'N/A')}, "
                    f"Warehouses={record.get('total_warehouses', 'N/A')}"
                )
        
        return "\n".join(summary)
    
    def _identify_issues(self, warehouse_data: Dict) -> List[Dict]:
        """Identify issues from warehouse data"""
        issues = []
        
        risk_score = warehouse_data.get('risk_score', 0)
        if risk_score > 0.7:
            issues.append({
                "type": "high_risk",
                "description": f"High risk score of {risk_score:.3f}",
                "severity": "critical"
            })
        
        infra = warehouse_data.get('infrastructure', {})
        if not infra.get('has_electric_backup'):
            issues.append({
                "type": "infrastructure",
                "description": "No electric backup system",
                "severity": "high"
            })
        
        if not infra.get('is_flood_proof'):
            issues.append({
                "type": "infrastructure",
                "description": "Not flood-proof",
                "severity": "medium"
            })
        
        risks = warehouse_data.get('risks', [])
        for risk in risks:
            if risk.get('count', 0) > 2:
                issues.append({
                    "type": "recurring_incident",
                    "description": f"Multiple {risk['type']} incidents ({risk['count']})",
                    "severity": "high"
                })
        
        return issues


if __name__ == "__main__":
    generator = AnswerGenerator()
    
    test_query = "Show me high-risk warehouses"
    test_results = [
        {"warehouse_id": "WH_0001", "risk_score": 0.85, "location": "city", "risk_count": 5},
        {"warehouse_id": "WH_0023", "risk_score": 0.78, "location": "village", "risk_count": 3}
    ]
    
    test_context = {"summary": "Analysis of high-risk warehouses", "related_entities": []}
    test_understanding = {"intent": "risk_identification", "complexity": "simple"}
    
    answer = generator.generate_answer(test_query, test_results, test_context, test_understanding)
    print("\n🤖 Generated Answer:")
    print(answer)
