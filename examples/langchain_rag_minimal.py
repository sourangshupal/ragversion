"""
Minimal RAGVersion + LangChain RAG Application

This script demonstrates how to integrate RAGVersion with LangChain
to build a simple RAG application that automatically keeps the vector
store in sync with document changes.

Prerequisites:
    pip install ragversion[langchain] openai faiss-cpu
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


async def setup_rag_system():
    """
    Set up a minimal RAG system with RAGVersion + LangChain.
    """

    # Step 1: Initialize RAGVersion tracker
    tracker = AsyncVersionTracker(
        storage=SupabaseStorage.from_env(),
        store_content=True,
        max_file_size_mb=50,
    )
    await tracker.initialize()

    # Step 2: Set up LangChain components
    embeddings = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    # Initialize FAISS vector store (or use Chroma, Pinecone, etc.)
    # Create from existing documents or initialize empty
    vectorstore_path = Path("./vectorstore_index")
    
    if vectorstore_path.exists():
        # Load existing vector store
        vectorstore = FAISS.load_local(
            str(vectorstore_path),
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        # Create new empty vector store
        vectorstore = FAISS.from_texts(
            ["Initial placeholder text - will be replaced"],
            embeddings
        )

    # Step 3: Integrate RAGVersion with LangChain
    sync = LangChainSync(
        tracker=tracker,
        text_splitter=text_splitter,
        embeddings=embeddings,
        vectorstore=vectorstore,
    )

    # Step 4: Sync documents (only changes will be processed)
    documents_dir = "./documents"
    
    print(f"Syncing documents from {documents_dir}...")
    await sync.sync_directory(
        documents_dir,
        patterns=["*.txt", "*.md", "*.pdf"],
        recursive=True,
        max_workers=4,
    )

    # Step 5: Save the updated vector store
    vectorstore.save_local(str(vectorstore_path))

    return tracker, vectorstore


def create_rag_chain(vectorstore):
    """
    Create a simple RAG chain using LangChain Expression Language (LCEL).
    """
    
    # Create retriever from vector store
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Define prompt template
    template = """
    You are a helpful assistant. Answer the question based on the following context:
    
    <Context>
    {context}
    </Context>
    
    Question: {question}
    
    Answer:
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    # Initialize LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # Build RAG chain using LCEL
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


async def main():
    """
    Main demonstration of the integrated RAG system.
    """
    
    print("=" * 60)
    print("RAGVersion + LangChain RAG Application")
    print("=" * 60)
    
    # Verify environment variables are set
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please set them in your .env file:")
        for var in missing:
            print(f"  {var}=your-value-here")
        return
    
    # Create sample documents directory if it doesn't exist
    documents_dir = Path("./documents")
    documents_dir.mkdir(exist_ok=True)
    
    # Create sample documents (for demonstration)
    sample_file = documents_dir / "sample.txt"
    if not sample_file.exists():
        sample_file.write_text("""
        RAGVersion is a version tracking system for RAG applications.
        It automatically detects document changes and keeps vector stores in sync.
        LangChain is a framework for building LLM-powered applications.
        Together, they create a powerful RAG system that stays up-to-date automatically.
        """)
        print(f"Created sample document: {sample_file}")
    
    # Set up the RAG system
    tracker, vectorstore = await setup_rag_system()
    
    # Create the RAG chain
    rag_chain = create_rag_chain(vectorstore)
    
    print("\n" + "=" * 60)
    print("RAG System Ready!")
    print("=" * 60)
    
    # Example queries
    questions = [
        "What is RAGVersion?",
        "How does it work with LangChain?",
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        print("-" * 60)
        
        try:
            answer = rag_chain.invoke(question)
            print(f"Answer: {answer}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Automatic Sync Demonstration")
    print("=" * 60)
    
    # Demonstrate automatic sync on document changes
    print("\nModifying sample document...")
    sample_file.write_text("""
    RAGVersion is a version tracking system for RAG applications.
    It automatically detects document changes and keeps vector stores in sync.
    LangChain is a framework for building LLM-powered applications.
    Together, they create a powerful RAG system that stays up-to-date automatically.
    
    NEW CONTENT: This information was added to demonstrate automatic syncing.
    RAGVersion will detect this change and update the vector store automatically.
    """)
    
    # Sync again (only the changed document will be processed)
    sync = LangChainSync(
        tracker=tracker,
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200),
        embeddings=OpenAIEmbeddings(),
        vectorstore=vectorstore,
    )
    
    print("Syncing changed documents...")
    await sync.sync_directory("./documents")
    
    # Save updated vector store
    vectorstore.save_local("./vectorstore_index")
    
    print("Vector store updated with changes!")
    
    # Test with new question about the added content
    new_question = "What happens when documents are modified?"
    print(f"\nQuestion: {new_question}")
    print("-" * 60)
    
    try:
        answer = rag_chain.invoke(new_question)
        print(f"Answer: {answer}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Clean up
    await tracker.close()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. RAGVersion automatically tracks document changes")
    print("2. LangChainSync updates vector store only for changed files")
    print("3. No need to reprocess entire knowledge base")
    print("4. Version history is maintained for audit trails")


if __name__ == "__main__":
    asyncio.run(main())
