"""
Graph Schema Definitions for Warehouse Risk Assessment
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class NodeType(Enum):
    WAREHOUSE = "Warehouse"
    MANAGER = "Manager"
    ZONE = "Zone"
    REGIONAL_ZONE = "RegionalZone"
    INFRASTRUCTURE = "Infrastructure"
    RISK_EVENT = "RiskEvent"
    MARKET_CONTEXT = "MarketContext"
    COMPLIANCE = "Compliance"

class RelationType(Enum):
    MANAGES = "MANAGES"
    LOCATED_IN = "LOCATED_IN"
    PART_OF = "PART_OF"
    HAS_INFRASTRUCTURE = "HAS_INFRASTRUCTURE"
    EXPERIENCED = "EXPERIENCED"
    VULNERABLE_TO = "VULNERABLE_TO"
    OPERATES_IN = "OPERATES_IN"
    SERVES = "SERVES"
    SUBJECT_TO = "SUBJECT_TO"
    REQUIRES_REFILL = "REQUIRES_REFILL"

@dataclass
class WarehouseNode:
    warehouse_id: str
    capacity_size: str
    established_year: int
    owner_type: str
    location_type: str
    distance_from_hub: float
    workers_count: int
    product_shipped_tons: float
    risk_score: Optional[float] = None

@dataclass
class RiskEventNode:
    event_id: str
    event_type: str
    severity: str
    occurrence_count: int
    time_period: str

@dataclass
class InfrastructureNode:
    infrastructure_id: str
    has_temp_regulation: bool
    has_electric_backup: bool
    is_flood_proof: bool
    certificate_type: str

@dataclass
class MarketContextNode:
    market_id: str
    competitor_count: int
    retail_shop_count: int
    distributor_count: int
    is_flood_impacted: bool

# Cypher Query Templates
CYPHER_SCHEMA = {
    "create_constraints": [
        "CREATE CONSTRAINT warehouse_id IF NOT EXISTS FOR (w:Warehouse) REQUIRE w.warehouse_id IS UNIQUE",
        "CREATE CONSTRAINT manager_id IF NOT EXISTS FOR (m:Manager) REQUIRE m.manager_id IS UNIQUE",
        "CREATE CONSTRAINT zone_id IF NOT EXISTS FOR (z:Zone) REQUIRE z.zone_id IS UNIQUE",
    ],
    
    "create_indexes": [
        "CREATE INDEX warehouse_capacity IF NOT EXISTS FOR (w:Warehouse) ON (w.capacity_size)",
        "CREATE INDEX risk_event_type IF NOT EXISTS FOR (r:RiskEvent) ON (r.event_type)",
        "CREATE INDEX warehouse_location IF NOT EXISTS FOR (w:Warehouse) ON (w.location_type)",
    ]
}