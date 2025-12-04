"""
Configuration Manager - Load settings from .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

class Config:
    """Configuration class to manage all settings from .env"""
    
    # Groq LLM Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')  # Changed from 'warehouse_risk' to 'neo4j'
    
    # Data Paths
    DATA_INPUT_CSV = os.getenv('DATA_INPUT_CSV', 'data/raw/warehouse_data.csv')
    DATA_PROCESSED_DIR = os.getenv('DATA_PROCESSED_DIR', 'data/processed/')
    
    # Embeddings Configuration
    EMBEDDINGS_MODEL = os.getenv('EMBEDDINGS_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    EMBEDDINGS_DIMENSION = int(os.getenv('EMBEDDINGS_DIMENSION', 384))
    EMBEDDINGS_BATCH_SIZE = int(os.getenv('EMBEDDINGS_BATCH_SIZE', 32))
    
    # Query Configuration
    MAX_RESULTS = int(os.getenv('MAX_RESULTS', 10))
    CONTEXT_WINDOW = int(os.getenv('CONTEXT_WINDOW', 5))
    ENABLE_MULTI_HOP = os.getenv('ENABLE_MULTI_HOP', 'true').lower() == 'true'
    
    # LLM Configuration
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', 0.1))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', 2000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/graphrag.log')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is not set in .env file")
        
        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD is not set in .env file")
        
        if not Path(cls.DATA_INPUT_CSV).exists():
            logger.warning(f"Data file not found: {cls.DATA_INPUT_CSV}")
        
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
        
        logger.info("✅ Configuration validated successfully")
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive data)"""
        print("\n" + "="*60)
        print("⚙️  CONFIGURATION")
        print("="*60)
        print(f"Groq Model: {cls.GROQ_MODEL}")
        print(f"Neo4j URI: {cls.NEO4J_URI}")
        print(f"Neo4j Database: {cls.NEO4J_DATABASE}")
        print(f"Data Input: {cls.DATA_INPUT_CSV}")
        print(f"Max Results: {cls.MAX_RESULTS}")
        print(f"Temperature: {cls.LLM_TEMPERATURE}")
        print("="*60 + "\n")

# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise