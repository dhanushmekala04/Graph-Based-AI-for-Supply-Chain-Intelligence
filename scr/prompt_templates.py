"""
11. SRC/PROMPT_TEMPLATES.PY - Complete Prompt Templates
"""

# Query Understanding Prompt
QUERY_UNDERSTANDING_PROMPT = """
Analyze this warehouse supply chain query and extract structured information:

Query: "{query}"

Return a JSON object with:
{{
    "intent": "<one of: risk_identification, performance_analysis, comparison, optimization, root_cause, prediction, exploration, reporting, filtering, aggregation, correlation, trend_analysis, anomaly_detection, compliance_check, capacity_analysis, location_analysis, manager_performance, infrastructure_assessment, market_analysis, general_lookup>",
    "entities": ["list of entities mentioned: warehouse_id, zone, manager, region, etc"],
    "risk_factors": ["breakdown", "storage_issue", "transport_issue", "flood", "power_outage", "temp_control", etc],
    "time_scope": "<current, historical, future, last_3m, last_6m, last_1y>",
    "graph_pattern": "<simple_lookup, multi_hop, aggregation, path_finding, subgraph, complex_join>",
    "complexity": "<basic, intermediate, advanced, expert>",
    "data_focus": ["warehouses", "managers", "zones", "infrastructure", "risk_events", "compliance", "market"],
    "output_format": "<summary, detailed, comparative, ranked, statistical>",
    "filters": ["risk_score > 0.7", "location_type = 'Urban'", "has_electric_backup = false"],
    "requires_comparison": <true/false>,
    "requires_aggregation": <true/false>,
    "requires_temporal_analysis": <true/false>,
    "requires_geospatial_analysis": <true/false>
}}

Be comprehensive and specific. Consider the full range of warehouse analytics questions.
Return ONLY valid JSON.
"""

# Cypher Generation Prompt
CYPHER_GENERATION_PROMPT = """
Generate a Neo4j Cypher query for this warehouse supply chain analytics question.

Intent: {intent}
Query: "{query}"
Entities: {entities}
Risk Factors: {risk_factors}

Graph Schema:
- Warehouse (warehouse_id, capacity_size, established_year, owner_type, location_type, distance_from_hub, workers_count, product_shipped_tons, risk_score)
- Manager (manager_id) -[:MANAGES]-> Warehouse
- Zone (zone_id, zone_name) <-[:PART_OF]- RegionalZone (regional_zone_id, regional_zone_name) <-[:LOCATED_IN]- Warehouse
- Infrastructure (infrastructure_id, has_temp_regulation, has_electric_backup, is_flood_proof, certificate_type) <-[:HAS_INFRASTRUCTURE]- Warehouse
- RiskEvent (event_id, event_type, occurrence_count, severity, time_period) <-[:EXPERIENCED]- Warehouse
- MarketContext (market_id, competitor_count, retail_shop_count, distributor_count, is_flood_impacted) <-[:OPERATES_IN]- Warehouse
- Compliance (compliance_id, govt_checks_l3m, certificate_type, refill_requests_l3m) <-[:SUBJECT_TO]- Warehouse

Query Understanding:
- Complexity: {complexity}
- Graph Pattern: {graph_pattern}
- Data Focus: {data_focus}
- Time Scope: {time_scope}
- Requires Comparison: {requires_comparison}
- Requires Aggregation: {requires_aggregation}

Guidelines:
1. Use MATCH for finding patterns, OPTIONAL MATCH for optional relationships
2. Use WHERE for filtering with appropriate conditions
3. Include ORDER BY and LIMIT for ranked results
4. Use aggregation functions (COUNT, AVG, SUM, MIN, MAX) when analyzing metrics
5. Use CASE statements for conditional logic and categorization
6. Include relevant properties with clear, descriptive aliases
7. Handle complex multi-hop relationships appropriately
8. Use parameters for dynamic values when possible
9. Ensure queries are efficient and avoid cartesian products
10. Return data in a format suitable for analysis

Return ONLY the Cypher query, no explanations or markdown formatting.
"""

# Answer Generation Prompt
ANSWER_GENERATION_PROMPT = """
Generate a comprehensive answer for this warehouse analysis query.

Query: "{query}"

Graph Query Results:
{results_summary}

Additional Context:
{context}

Instructions:
1. Provide a clear, direct answer to the question
2. Include specific data points and metrics
3. Highlight key insights and patterns
4. Use bullet points for multiple items
5. Be concise but informative
6. Include risk levels when relevant (Low/Medium/High/Critical)

Format your answer professionally for a business audience.
"""

# Risk Assessment Prompt
RISK_ASSESSMENT_PROMPT = """
Provide a detailed risk assessment for this warehouse.

Warehouse ID: {warehouse_id}
Risk Score: {risk_score}

Incidents:
{incidents}

Infrastructure:
{infrastructure}

Market Context:
{market}

Generate a comprehensive risk assessment including:
1. Overall Risk Level (Low/Medium/High/Critical)
2. Key Risk Factors
3. Infrastructure Gaps
4. Market Challenges
5. Priority Action Items

Be specific and actionable.
"""

# Recommendation Prompt
RECOMMENDATION_PROMPT = """
Generate actionable recommendations for warehouse improvement.

Current State:
{current_state}

Identified Issues:
{issues}

Benchmark Data (Similar Warehouses):
{benchmarks}

Provide:
1. Top 3-5 Priority Recommendations
2. Expected Impact (High/Medium/Low)
3. Implementation Difficulty (Easy/Medium/Hard)
4. Estimated Timeline
5. Success Metrics

Focus on practical, implementable solutions.
"""

# Comparison Prompt
COMPARISON_PROMPT = """
Generate a comparative analysis of these warehouses.

Warehouses Data:
{warehouses}

Comparison Metrics:
{metrics}

Provide:
1. Key Differences
2. Performance Rankings
3. Best Practices Identified
4. Areas for Improvement
5. Recommendations for Lower Performers

Use clear comparisons and data-driven insights.
"""

# Context Extraction Prompt
CONTEXT_EXTRACTION_PROMPT = """
Extract and summarize key information from these graph query results.

Query: "{query}"

Results:
{results}

Provide a concise summary (2-3 sentences) highlighting:
- Number of results
- Key patterns or trends
- Notable outliers or anomalies
- Most important insights

Be factual and data-focused.
"""
