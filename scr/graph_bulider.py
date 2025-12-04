"""
Graph Builder - Construct Neo4j graph from extracted entities
"""

from neo4j import GraphDatabase
from typing import Dict, List
from loguru import logger
from tqdm import tqdm

from config import Config

class GraphBuilder:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
        )
        self.database = Config.NEO4J_DATABASE if Config.NEO4J_DATABASE != 'warehouse_risk' else None
        
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear existing graph data"""
        logger.warning("Clearing database...")
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared")
    
    def create_constraints(self):
        """Create uniqueness constraints and indexes"""
        logger.info("Creating constraints and indexes...")
        
        constraints = [
            "CREATE CONSTRAINT warehouse_id IF NOT EXISTS FOR (w:Warehouse) REQUIRE w.warehouse_id IS UNIQUE",
            "CREATE CONSTRAINT manager_id IF NOT EXISTS FOR (m:Manager) REQUIRE m.manager_id IS UNIQUE",
            "CREATE CONSTRAINT zone_id IF NOT EXISTS FOR (z:Zone) REQUIRE z.zone_id IS UNIQUE",
            "CREATE CONSTRAINT regional_zone_id IF NOT EXISTS FOR (rz:RegionalZone) REQUIRE rz.regional_zone_id IS UNIQUE",
        ]
        
        with self.driver.session(database=self.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint already exists: {e}")
        
        logger.info("✅ Constraints created")
    
    def create_warehouse_nodes(self, warehouses: List[Dict]):
        """Create Warehouse nodes"""
        logger.info(f"Creating {len(warehouses)} warehouse nodes...")
        
        query = """
        UNWIND $warehouses AS wh
        CREATE (w:Warehouse {
            warehouse_id: wh.warehouse_id,
            capacity_size: wh.capacity_size,
            established_year: wh.established_year,
            owner_type: wh.owner_type,
            location_type: wh.location_type,
            distance_from_hub: wh.distance_from_hub,
            workers_count: wh.workers_count,
            product_shipped_tons: wh.product_shipped_tons,
            risk_score: wh.risk_score
        })
        """
        
        with self.driver.session(database=self.database) as session:
            session.run(query, warehouses=warehouses)
        
        logger.info("✅ Warehouse nodes created")
    
    def create_manager_nodes(self, managers: List[Dict]):
        """Create Manager nodes and MANAGES relationships"""
        logger.info(f"Creating {len(managers)} manager nodes...")
        
        query = """
        UNWIND $managers AS mgr
        MERGE (m:Manager {manager_id: mgr.manager_id})
        WITH m, mgr
        MATCH (w:Warehouse {warehouse_id: mgr.warehouse_id})
        CREATE (m)-[:MANAGES]->(w)
        """
        
        with self.driver.session(database=self.database) as session:
            session.run(query, managers=managers)
        
        logger.info("✅ Manager nodes and relationships created")
    
    def create_zone_hierarchy(self, zones: List[Dict], regional_zones: List[Dict]):
        """Create Zone and RegionalZone nodes with hierarchy"""
        logger.info("Creating zone hierarchy...")
        
        zone_query = """
        UNWIND $zones AS z
        MERGE (zone:Zone {zone_id: z.zone_id})
        SET zone.zone_name = z.zone_name
        """
        
        regional_query = """
        UNWIND $regional_zones AS rz
        MERGE (region:RegionalZone {regional_zone_id: rz.regional_zone_id})
        SET region.regional_zone_name = rz.regional_zone_name
        WITH region, rz
        MATCH (z:Zone {zone_id: 'ZONE_' + rz.parent_zone})
        MERGE (region)-[:PART_OF]->(z)
        WITH region, rz
        MATCH (w:Warehouse {warehouse_id: rz.warehouse_id})
        MERGE (w)-[:LOCATED_IN]->(region)
        """
        
        with self.driver.session(database=self.database) as session:
            session.run(zone_query, zones=zones)
            session.run(regional_query, regional_zones=regional_zones)
        
        logger.info("✅ Zone hierarchy created")
    
    def create_infrastructure_nodes(self, infrastructures: List[Dict]):
        """Create Infrastructure nodes"""
        logger.info(f"Creating {len(infrastructures)} infrastructure nodes...")
        
        with self.driver.session(database=self.database) as session:
            for inf in infrastructures:
                query = """
                CREATE (i:Infrastructure {
                    infrastructure_id: $inf_id,
                    has_temp_regulation: $temp_reg,
                    has_electric_backup: $electric_backup,
                    is_flood_proof: $flood_proof,
                    certificate_type: $cert_type
                })
                WITH i
                MATCH (w:Warehouse {warehouse_id: $warehouse_id})
                CREATE (w)-[:HAS_INFRASTRUCTURE]->(i)
                """
                
                session.run(query, {
                    'inf_id': str(inf['infrastructure_id']),
                    'temp_reg': bool(inf['has_temp_regulation']),
                    'electric_backup': bool(inf['has_electric_backup']),
                    'flood_proof': bool(inf['is_flood_proof']),
                    'cert_type': str(inf['certificate_type']),
                    'warehouse_id': str(inf['warehouse_id'])
                })
        
        logger.info("✅ Infrastructure nodes created")
    
    def create_risk_event_nodes(self, risk_events: List[Dict]):
        """Create RiskEvent nodes"""
        logger.info(f"Creating {len(risk_events)} risk event nodes...")
        
        query = """
        UNWIND $risk_events AS risk
        CREATE (r:RiskEvent {
            event_id: risk.event_id,
            event_type: risk.event_type,
            occurrence_count: risk.occurrence_count,
            severity: risk.severity,
            time_period: risk.time_period
        })
        WITH r, risk
        MATCH (w:Warehouse {warehouse_id: risk.warehouse_id})
        CREATE (w)-[:EXPERIENCED {
            count: risk.occurrence_count,
            severity: risk.severity
        }]->(r)
        """
        
        with self.driver.session(database=self.database) as session:
            session.run(query, risk_events=risk_events)
        
        logger.info("✅ Risk event nodes created")
    
    def create_market_context_nodes(self, market_contexts: List[Dict]):
        """Create MarketContext nodes"""
        logger.info(f"Creating {len(market_contexts)} market context nodes...")
        
        query = """
        UNWIND $market_contexts AS mkt
        CREATE (m:MarketContext {
            market_id: mkt.market_id,
            competitor_count: mkt.competitor_count,
            retail_shop_count: mkt.retail_shop_count,
            distributor_count: mkt.distributor_count,
            is_flood_impacted: mkt.is_flood_impacted
        })
        WITH m, mkt
        MATCH (w:Warehouse {warehouse_id: mkt.warehouse_id})
        CREATE (w)-[:OPERATES_IN]->(m)
        """
        
        with self.driver.session(database=self.database) as session:
            session.run(query, market_contexts=market_contexts)
        
        logger.info("✅ Market context nodes created")
    
    def create_compliance_nodes(self, compliances: List[Dict]):
        """Create Compliance nodes"""
        logger.info(f"Creating {len(compliances)} compliance nodes...")
        
        query = """
        UNWIND $compliances AS comp
        CREATE (c:Compliance {
            compliance_id: comp.compliance_id,
            govt_checks_l3m: comp.govt_checks_l3m,
            certificate_type: comp.certificate_type,
            refill_requests_l3m: comp.refill_requests_l3m
        })
        WITH c, comp
        MATCH (w:Warehouse {warehouse_id: comp.warehouse_id})
        CREATE (w)-[:SUBJECT_TO]->(c)
        """
        
        with self.driver.session(database=self.database) as session:
            session.run(query, compliances=compliances)
        
        logger.info("✅ Compliance nodes created")
    
    def build_graph(self, entities: Dict[str, List[Dict]], clear_existing: bool = True):
        """Build complete graph from entities"""
        logger.info("🏗️  Starting graph construction...")
        
        if clear_existing:
            self.clear_database()
        
        self.create_constraints()
        self.create_warehouse_nodes(entities['warehouses'])
        self.create_manager_nodes(entities['managers'])
        self.create_zone_hierarchy(entities['zones'], entities['regional_zones'])
        self.create_infrastructure_nodes(entities['infrastructures'])
        self.create_risk_event_nodes(entities['risk_events'])
        self.create_market_context_nodes(entities['market_contexts'])
        self.create_compliance_nodes(entities['compliances'])
        
        # Verify graph
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            logger.info("\n📊 Graph Statistics:")
            for record in result:
                logger.info(f"  {record['label']}: {record['count']}")
        
        logger.info("✅ Graph construction completed!")

if __name__ == "__main__":
    from ingestion import DataIngestion
    
    ingestion = DataIngestion()
    df, entities = ingestion.run_pipeline()
    
    builder = GraphBuilder()
    try:
        builder.build_graph(entities)
    finally:
        builder.close()