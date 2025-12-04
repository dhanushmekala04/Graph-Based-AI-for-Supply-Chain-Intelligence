import sys
from pathlib import Path
from loguru import logger

# Add scr directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'scr'))

from scr.config import Config
from scr.ingestion import DataIngestion
from scr.graph_bulider import GraphBuilder
from scr.pipeline import GraphRAGPipeline

from time import time

def setup_logging():
    """Configure logging"""
    log_path = Path(Config.LOG_FILE)
    log_path.parent.mkdir(exist_ok=True, parents=True)
    
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=Config.LOG_LEVEL
    )
    logger.add(
        Config.LOG_FILE,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )


def initialize_graph():
    """Initialize graph database with data"""
    logger.info("🚀 Initializing graph database...")
    
    # Step 1: Data Ingestion
    logger.info("Step 1: Data Ingestion")
    ingestion = DataIngestion()
    df, entities = ingestion.run_pipeline()
    
    # Step 2: Graph Construction
    logger.info("Step 2: Graph Construction")
    builder = GraphBuilder()
    try:
        builder.build_graph(entities, clear_existing=True)
    finally:
        builder.close()
    
    logger.info("✅ Graph initialization completed!")
    return df, entities


def run_interactive_mode(pipeline: GraphRAGPipeline):
    """Run interactive query mode"""
    logger.info("\n" + "="*60)
    logger.info("🤖 GraphRAG Interactive Mode")
    logger.info("="*60)
    print("\nType your questions about warehouses (or 'quit' to exit)")
    print("Example: 'Show me high-risk warehouses in flood zones'\n")
    
    while True:
        try:
            query = input("\n💬 Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if not query:
                continue
            
            # Process query
            result = pipeline.process_query(query, generate_recommendations=True)
            
            # Display results
            print("\n" + "="*60)
            print("🤖 ANSWER:")
            print("="*60)
            print(result['answer'])
            
            if result.get('recommendations'):
                print("\n📋 RECOMMENDATIONS:")
                for rec in result['recommendations']:
                    print(f"\n  Warehouse: {rec['warehouse_id']}")
                    print(f"  Priority: {rec['priority']}")
                    print(f"  Actions:")
                    for action in rec['actions']:
                        print(f"    - {action}")
            
            print("\n" + "="*60)
            print(f"Results: {result['result_count']} | Time: {result['metadata']['processing_time_seconds']}s")
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\n❌ Error: {e}")


def run_demo_queries(pipeline: GraphRAGPipeline):
    """Run demonstration queries"""
    demo_queries = [
        "Show me the top 5 highest risk warehouses",
        "Which warehouses are in flood-prone areas without flood protection?",
        "Compare risk levels across different zones",
        "What warehouses have had the most breakdowns?",
        "Show me warehouses with poor infrastructure in high-competitor markets"
    ]
    
    logger.info("\n" + "="*60)
    logger.info("🎯 Running Demo Queries")
    logger.info("="*60)
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n\n{'='*60}")
        print(f"Demo Query {i}/{len(demo_queries)}: {query}")
        print('='*60)
        
        result = pipeline.process_query(query)
        
        print(f"\n🤖 Answer:\n{result['answer']}")
        print(f"\n📊 Found {result['result_count']} results in {result['metadata']['processing_time_seconds']}s")


def main():
    """Main application entry point"""
    setup_logging()
    
    print("\n" + "="*60)
    print("🏭 FMCG Supply Chain GraphRAG System")
    print("="*60)
    
    # Display configuration
    Config.print_config()
    
    # Check if initialization is needed
    initialize = input("\n🔧 Initialize graph database? (yes/no): ").strip().lower()
    
    if initialize in ['yes', 'y']:
        try:
            initialize_graph()
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return
    
    # Create pipeline
    logger.info("\n🚀 Starting GraphRAG Pipeline...")
    pipeline = GraphRAGPipeline()
    
    try:
        # Choose mode
        print("\n📍 Select Mode:")
        print("  1. Interactive Query Mode")
        print("  2. Run Demo Queries")
        print("  3. Exit")
        
        choice = input("\nChoice (1/2/3): ").strip()
        
        if choice == '1':
            run_interactive_mode(pipeline)
        elif choice == '2':
            run_demo_queries(pipeline)
        else:
            print("Goodbye! 👋")
    
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()