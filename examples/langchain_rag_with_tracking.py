"""
Enhanced RAGVersion + LangChain RAG with Change Tracking

This script shows how to track document changes in real-time
and see exactly what chunks were added/modified in your RAG system.

Key Features:
- Real-time change tracking during sync
- Display version history for each document
- Show which chunks were created/modified
- Compare versions to see differences
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from ragversion import AsyncVersionTracker
from ragversion.storage import SupabaseStorage
from ragversion.integrations.langchain import LangChainSync


class ChangeTracker:
    """
    Helper class to track and display document changes.
    """
    
    def __init__(self, tracker, text_splitter):
        self.tracker = tracker
        self.text_splitter = text_splitter
        self.changes_detected = []
    
    async def track_changes(self, file_path):
        """
        Track changes for a specific file and return detailed information.
        
        Returns:
            dict: Detailed change information including chunks
        """
        normalized_path = str(Path(file_path).absolute())
        
        # Get document info
        doc = await self.tracker.storage.get_document_by_path(normalized_path)
        
        if not doc:
            return {
                "file_path": file_path,
                "status": "NEW_DOCUMENT",
                "message": "New document detected"
            }
        
        # Get latest version
        latest_version = await self.tracker.storage.get_latest_version(doc.id)
        
        # Get content
        content = await self.tracker.storage.get_content(latest_version.id)
        
        # Analyze chunks
        chunks = self.text_splitter.split_text(content) if content else []
        
        # Calculate chunk hashes
        import hashlib
        chunk_info = []
        for idx, chunk in enumerate(chunks, 1):
            chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()[:16]
            chunk_info.append({
                "index": idx,
                "size": len(chunk),
                "hash": chunk_hash,
                "preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
            })
        
        change_info = {
            "file_path": file_path,
            "document_id": str(doc.id),
            "file_name": doc.file_name,
            "status": latest_version.change_type.value.upper(),
            "version_number": latest_version.version_number,
            "content_length": len(content) if content else 0,
            "file_size": doc.file_size,
            "total_chunks": len(chunks),
            "chunks": chunk_info,
            "created_at": latest_version.created_at,
            "content_hash": latest_version.content_hash
        }
        
        self.changes_detected.append(change_info)
        return change_info
    
    async def compare_with_previous(self, file_path):
        """
        Compare current version with previous version.
        
        Returns:
            dict: Comparison information
        """
        normalized_path = str(Path(file_path).absolute())
        doc = await self.tracker.storage.get_document_by_path(normalized_path)
        
        if not doc or doc.current_version <= 1:
            return {
                "file_path": file_path,
                "message": "No previous version to compare"
            }
        
        # Get current and previous versions
        current_version = await self.tracker.storage.get_version_by_number(
            doc.id, doc.current_version
        )
        previous_version = await self.tracker.storage.get_version_by_number(
            doc.id, doc.current_version - 1
        )
        
        # Get content
        current_content = await self.tracker.storage.get_content(current_version.id)
        previous_content = await self.tracker.storage.get_content(previous_version.id)
        
        # Analyze chunks
        current_chunks = self.text_splitter.split_text(current_content) if current_content else []
        previous_chunks = self.text_splitter.split_text(previous_content) if previous_content else []
        
        # Calculate chunk differences
        import hashlib
        current_hashes = {
            hashlib.sha256(chunk.encode()).hexdigest()[:16]: chunk 
            for chunk in current_chunks
        }
        previous_hashes = {
            hashlib.sha256(chunk.encode()).hexdigest()[:16]: chunk 
            for chunk in previous_chunks
        }
        
        new_chunks = set(current_hashes.keys()) - set(previous_hashes.keys())
        removed_chunks = set(previous_hashes.keys()) - set(current_hashes.keys())
        
        return {
            "file_path": file_path,
            "current_version": current_version.version_number,
            "previous_version": previous_version.version_number,
            "total_current_chunks": len(current_chunks),
            "total_previous_chunks": len(previous_chunks),
            "new_chunks": len(new_chunks),
            "removed_chunks": len(removed_chunks),
            "new_chunk_hashes": list(new_chunks),
            "removed_chunk_hashes": list(removed_chunks),
            "content_length_diff": len(current_content or "") - len(previous_content or "")
        }
    
    def print_change_summary(self):
        """
        Print a summary of all detected changes.
        """
        print("\n" + "=" * 70)
        print("CHANGE SUMMARY")
        print("=" * 70)
        
        if not self.changes_detected:
            print("No changes detected")
            return
        
        print(f"\nTotal Files Changed: {len(self.changes_detected)}\n")
        
        for idx, change in enumerate(self.changes_detected, 1):
            print(f"{idx}. {change['file_name']}")
            print(f"   Status: {change['status']}")
            print(f"   Version: {change.get('version_number', 'N/A')}")
            print(f"   Content: {change.get('content_length', 0)} chars")
            print(f"   Chunks Created: {change.get('total_chunks', 0)}")
            
            if change.get('chunks'):
                print(f"   Chunk Details:")
                for chunk in change['chunks'][:3]:  # Show first 3 chunks
                    print(f"      Chunk {chunk['index']}: {chunk['size']} chars, hash={chunk['hash']}")
                if len(change['chunks']) > 3:
                    print(f"      ... and {len(change['chunks']) - 3} more chunks")
            
            print()
    
    def print_chunk_details(self, change_info):
        """
        Print detailed information about chunks for a specific change.
        """
        print(f"\n{'='*70}")
        print(f"CHUNK DETAILS: {change_info['file_name']}")
        print(f"Status: {change_info['status']} | Version: {change_info.get('version_number', 'N/A')}")
        print(f"{'='*70}")
        
        if not change_info.get('chunks'):
            print("No chunks created")
            return
        
        print(f"\nTotal Chunks: {change_info['total_chunks']}")
        print(f"Total Content: {change_info['content_length']} characters")
        print(f"Average Chunk Size: {change_info['content_length'] // change_info['total_chunks']} chars\n")
        
        for chunk in change_info['chunks']:
            print(f"📦 Chunk {chunk['index']}:")
            print(f"   ├─ Size: {chunk['size']} characters")
            print(f"   ├─ Hash: {chunk['hash']}")
            print(f"   └─ Preview: {chunk['preview']}")
            print()


async def setup_rag_system_with_tracking():
    """
    Set up RAG system with change tracking enabled.
    """
    
    # Initialize tracker
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env(),
        store_content=True,
        max_file_size_mb=50,
    )
    await tracker.initialize()
    
    # Setup LangChain components
    embeddings = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    
    # Initialize change tracker
    change_tracker = ChangeTracker(tracker, text_splitter)
    
    # Initialize vector store
    vectorstore_path = Path("./vectorstore_index")
    
    if vectorstore_path.exists():
        vectorstore = FAISS.load_local(
            str(vectorstore_path),
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        vectorstore = FAISS.from_texts(["Initial placeholder"], embeddings)
    
    # Setup LangChain sync
    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore,
    )
    
    return tracker, vectorstore, sync, change_tracker


def create_rag_chain(vectorstore):
    """Create RAG chain."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    template = """
    You are a helpful assistant. Answer based on context:
    
    <Context>
    {context}
    </Context>
    
    Question: {question}
    Answer:
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain


async def main():
    """
    Main demonstration with change tracking.
    """
    
    print("=" * 70)
    print("RAGVersion + LangChain with Change Tracking")
    print("=" * 70)
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        return
    
    # Setup
    tracker, vectorstore, sync, change_tracker = await setup_rag_system_with_tracking()
    
    # Create documents directory
    documents_dir = Path("./documents")
    documents_dir.mkdir(exist_ok=True)
    
    # Create sample document
    sample_file = documents_dir / "sample.txt"
    if not sample_file.exists():
        sample_file.write_text("""
        RAGVersion is a version tracking system for RAG applications.
        It automatically detects document changes and keeps vector stores in sync.
        """)
        print(f"Created sample document: {sample_file}")
    
    try:
        # First sync - track changes
        print("\n" + "=" * 70)
        print("INITIAL SYNC - Tracking Changes")
        print("=" * 70)
        
        await sync.sync_directory("./documents", patterns=["*.txt"])
        
        # Track changes for all documents
        for txt_file in documents_dir.glob("*.txt"):
            change_info = await change_tracker.track_changes(str(txt_file))
            if change_info.get('total_chunks', 0) > 0:
                change_tracker.print_chunk_details(change_info)
        
        # Save vector store
        vectorstore.save_local("./vectorstore_index")
        
        # Print summary
        change_tracker.print_change_summary()
        
        # Test RAG queries
        rag_chain = create_rag_chain(vectorstore)
        
        questions = [
            "What is RAGVersion?",
            "How does it work?",
        ]
        
        print("\n" + "=" * 70)
        print("RAG QUERIES")
        print("=" * 70)
        
        for question in questions:
            print(f"\nQ: {question}")
            answer = rag_chain.invoke(question)
            print(f"A: {answer}")
        
        # Modify document and track changes again
        print("\n" + "=" * 70)
        print("MODIFYING DOCUMENT - Tracking New Changes")
        print("=" * 70)
        
        print("\nModifying sample.txt...")
        sample_file.write_text("""
        RAGVersion is a version tracking system for RAG applications.
        It automatically detects document changes and keeps vector stores in sync.
        
        NEW SECTION: This is new content that was added.
        It demonstrates how RAGVersion tracks modifications and updates chunks.
        """)
        
        # Reset change tracker
        change_tracker.changes_detected = []
        
        # Sync again
        await sync.sync_directory("./documents", patterns=["*.txt"])
        
        # Track changes
        for txt_file in documents_dir.glob("*.txt"):
            change_info = await change_tracker.track_changes(str(txt_file))
            
            # Compare with previous version
            comparison = await change_tracker.compare_with_previous(str(txt_file))
            
            if comparison.get('new_chunks', 0) > 0:
                print(f"\n📊 Version Comparison for {txt_file.name}:")
                print(f"   Previous: {comparison['previous_version']} chunks ({comparison['total_previous_chunks']})")
                print(f"   Current: {comparison['current_version']} chunks ({comparison['total_current_chunks']})")
                print(f"   New Chunks: {comparison['new_chunks']}")
                print(f"   Removed Chunks: {comparison['removed_chunks']}")
                print(f"   Content Change: {comparison['content_length_diff']:+d} characters")
            
            if change_info.get('total_chunks', 0) > 0:
                change_tracker.print_chunk_details(change_info)
        
        # Save updated vector store
        vectorstore.save_local("./vectorstore_index")
        
        # Print final summary
        change_tracker.print_change_summary()
        
        # Test with new question
        print("\n" + "=" * 70)
        print("QUERYING UPDATED KNOWLEDGE BASE")
        print("=" * 70)
        
        new_question = "What happens when documents are modified?"
        print(f"\nQ: {new_question}")
        answer = rag_chain.invoke(new_question)
        print(f"A: {answer}")
        
        print("\n" + "=" * 70)
        print("DEMO COMPLETE!")
        print("=" * 70)
        
        print("\nKey Takeaways:")
        print("✅ Track exactly which chunks were created/modified")
        print("✅ See version-by-version changes for each document")
        print("✅ Compare previous vs current versions")
        print("✅ Monitor content length changes and chunk differences")
        print("✅ View chunk hashes to track specific pieces of content")
        
    finally:
        await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
