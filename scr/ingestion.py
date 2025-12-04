"""
Data Ingestion Pipeline - Load CSV and prepare for graph construction
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from loguru import logger
from pathlib import Path

from config import Config

class DataIngestion:
    def __init__(self):
        self.csv_path = Config.DATA_INPUT_CSV
        self.processed_dir = Config.DATA_PROCESSED_DIR
        self.df = None
        
    def load_data(self) -> pd.DataFrame:
        """Load warehouse dataset from CSV"""
        logger.info(f"Loading data from {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        logger.info(f"Loaded {len(self.df)} warehouse records")
        return self.df
    
    def clean_data(self) -> pd.DataFrame:
        """Clean and preprocess data"""
        logger.info("Cleaning data...")
        
        # Handle missing values
        self.df = self.df.fillna({
            'temp_reg_mach': 0,
            'electric_supply': 0,
            'flood_proof': 0,
            'approved_wh_govt_certificate': 'None',
            'wh_breakdown_l3m': 0,
            'storage_issue_reported_l3m': 0,
            'transport_issue_l1y': 0
        })
        
        # Convert boolean fields
        bool_columns = ['temp_reg_mach', 'electric_supply', 'flood_proof', 'flood_impacted']
        for col in bool_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(bool)
        
        # Create unique IDs
        if 'Ware_house_ID' not in self.df.columns:
            self.df['Ware_house_ID'] = [f"WH_{i:04d}" for i in range(len(self.df))]
        
        logger.info("Data cleaning completed")
        return self.df
    
    def calculate_risk_scores(self) -> pd.DataFrame:
        """Calculate composite risk scores"""
        logger.info("Calculating risk scores...")
        
        # Risk Score Components
        breakdown_risk = self.df.get('wh_breakdown_l3m', 0) / 10.0
        storage_risk = self.df.get('storage_issue_reported_l3m', 0) / 5.0
        transport_risk = self.df.get('transport_issue_l1y', 0).astype(float)
        
        # Infrastructure protection factor
        protection_factor = (
            self.df.get('temp_reg_mach', 0).astype(float) * 0.3 +
            self.df.get('electric_supply', 0).astype(float) * 0.3 +
            self.df.get('flood_proof', 0).astype(float) * 0.4
        )
        
        # Environmental risk factor
        env_risk = self.df.get('flood_impacted', 0).astype(float) * 0.5
        
        # Composite risk score (0-1 scale)
        self.df['risk_score'] = np.clip(
            (breakdown_risk * 0.4 + storage_risk * 0.3 + transport_risk * 0.2 + env_risk * 0.1) * 
            (1 - protection_factor * 0.3),
            0, 1
        )
        
        logger.info(f"Risk scores calculated. Mean: {self.df['risk_score'].mean():.3f}")
        return self.df
    
    def create_entity_extracts(self) -> Dict[str, List[Dict]]:
        """Extract entities for each node type"""
        logger.info("Extracting entities...")
        
        entities = {
            'warehouses': [],
            'managers': [],
            'zones': [],
            'regional_zones': [],
            'infrastructures': [],
            'risk_events': [],
            'market_contexts': [],
            'compliances': []
        }
        
        for idx, row in self.df.iterrows():
            wh_id = row['Ware_house_ID']
            
            # Warehouse Entity
            entities['warehouses'].append({
                'warehouse_id': wh_id,
                'capacity_size': row.get('WH_capacity_size', 'Unknown'),
                'established_year': int(float(row.get('wh_est_year', 2000))) if pd.notna(row.get('wh_est_year')) else 2000,
                'owner_type': row.get('wh_owner_type', 'Unknown'),
                'location_type': row.get('Location_type', 'Unknown'),
                'distance_from_hub': float(row.get('dist_from_hub', 0)),
                'workers_count': int(float(row.get('workers_num', 0))) if pd.notna(row.get('workers_num')) else 0,
                'product_shipped_tons': float(row.get('product_wg_ton', 0)),
                'risk_score': float(row.get('risk_score', 0))
            })
            
            # Manager Entity
            if pd.notna(row.get('WH_Manager_ID')):
                entities['managers'].append({
                    'manager_id': row['WH_Manager_ID'],
                    'warehouse_id': wh_id
                })
            
            # Zone Entities
            if pd.notna(row.get('zone')):
                entities['zones'].append({
                    'zone_id': f"ZONE_{row['zone']}",
                    'zone_name': row['zone']
                })
            
            if pd.notna(row.get('WH_regional_zone')):
                entities['regional_zones'].append({
                    'regional_zone_id': f"RZ_{row['WH_regional_zone']}",
                    'regional_zone_name': row['WH_regional_zone'],
                    'parent_zone': row.get('zone', 'Unknown'),
                    'warehouse_id': wh_id
                })
            
            # Infrastructure Entity
            entities['infrastructures'].append({
                'infrastructure_id': str(f"INF_{wh_id}"),
                'warehouse_id': str(wh_id),
                'has_temp_regulation': bool(int(row.get('temp_reg_mach', 0))),
                'has_electric_backup': bool(int(row.get('electric_supply', 0))),
                'is_flood_proof': bool(int(row.get('flood_proof', 0))),
                'certificate_type': str(row.get('approved_wh_govt_certificate', 'None'))
            })
            
            # Risk Events
            if row.get('wh_breakdown_l3m', 0) > 0:
                entities['risk_events'].append({
                    'event_id': f"RISK_BREAKDOWN_{wh_id}",
                    'warehouse_id': wh_id,
                    'event_type': 'breakdown',
                    'occurrence_count': int(row['wh_breakdown_l3m']),
                    'severity': 'high' if row['wh_breakdown_l3m'] > 2 else 'medium',
                    'time_period': 'l3m'
                })
            
            if row.get('storage_issue_reported_l3m', 0) > 0:
                entities['risk_events'].append({
                    'event_id': f"RISK_STORAGE_{wh_id}",
                    'warehouse_id': wh_id,
                    'event_type': 'storage_issue',
                    'occurrence_count': int(row['storage_issue_reported_l3m']),
                    'severity': 'medium',
                    'time_period': 'l3m'
                })
            
            if row.get('transport_issue_l1y', 0) > 0:
                entities['risk_events'].append({
                    'event_id': f"RISK_TRANSPORT_{wh_id}",
                    'warehouse_id': wh_id,
                    'event_type': 'transport_issue',
                    'occurrence_count': 1,
                    'severity': 'high',
                    'time_period': 'l1y'
                })
            
            # Market Context
            entities['market_contexts'].append({
                'market_id': f"MKT_{wh_id}",
                'warehouse_id': wh_id,
                'competitor_count': int(row.get('Competitor_in_mkt', 0)),
                'retail_shop_count': int(row.get('retail_shop_num', 0)),
                'distributor_count': int(row.get('distributor_num', 0)),
                'is_flood_impacted': bool(row.get('flood_impacted', 0))
            })
            
            # Compliance
            entities['compliances'].append({
                'compliance_id': f"COMP_{wh_id}",
                'warehouse_id': wh_id,
                'govt_checks_l3m': int(row.get('govt_check_l3m', 0)),
                'certificate_type': row.get('approved_wh_govt_certificate', 'None'),
                'refill_requests_l3m': int(row.get('num_refill_req_l3m', 0))
            })
        
        # Deduplicate
        entities['managers'] = list({m['manager_id']: m for m in entities['managers']}.values())
        entities['zones'] = list({z['zone_id']: z for z in entities['zones']}.values())
        
        logger.info(f"Extracted {sum(len(v) for v in entities.values())} total entities")
        return entities
    
    def run_pipeline(self) -> Tuple[pd.DataFrame, Dict]:
        """Execute full ingestion pipeline"""
        self.load_data()
        self.clean_data()
        self.calculate_risk_scores()
        entities = self.create_entity_extracts()
        
        # Save processed data
        output_path = Path(self.processed_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        self.df.to_csv(output_path / 'processed_warehouses.csv', index=False)
        
        logger.info("✅ Ingestion pipeline completed")
        return self.df, entities

if __name__ == "__main__":
    ingestion = DataIngestion()
    df, entities = ingestion.run_pipeline()
    print(f"\n📊 Summary:")
    print(f"  Warehouses: {len(entities['warehouses'])}")
    print(f"  Managers: {len(entities['managers'])}")
    print(f"  Risk Events: {len(entities['risk_events'])}")
    print(f"  Mean Risk Score: {df['risk_score'].mean():.3f}")