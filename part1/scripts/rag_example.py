# warning
import warnings

warnings.filterwarnings("ignore")

import os
from together import Together
import faiss

from sentence_transformers import SentenceTransformer

"""
Do these steps:
1) Set up a Together API key from https://together.ai/
"""
together_api_key = os.environ.get("TOGETHER_API_KEY")


def run_rag(data_dict: dict, prompt: str):
    """
    Run RAG system: process documents, create embeddings, search, and generate answer.

    """

    # Stage 0: Initialize Together AI client for LLM completions
    client = Together(api_key=together_api_key)

    # Stage 1: Load sentence transformer model for creating embeddings
    # ------------------------------------------------------------
    embedding_model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        use_auth_token=os.environ.get("HUGGINGFACE_HUB_TOKEN"),
    )

    # Stage 2: Process documents into Vector Database
    # ------------------------------------------------------------
    documents = []
    filenames = []

    print(f"Processing {len(data_dict)} documents...")
    for key, content in data_dict.items():
        content = content.strip()
        if content:  # Only add non-empty documents
            documents.append(content)
            filenames.append(key)
            print(f"✅ Loaded: {key}")

    if not documents:
        return "No valid documents found in data dictionary!"

    # Create embeddings for all documents
    print("Creating embeddings...")
    embeddings = embedding_model.encode(documents)

    # Set up FAISS index for similarity search
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)

    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    print(f"✅ RAG system ready with {len(documents)} documents!")

    # Stage 3: Retrieve relevant documents
    # ------------------------------------------------------------
    query_embedding = embedding_model.encode([prompt])
    faiss.normalize_L2(query_embedding)

    # Get top similar documents
    scores, indices = index.search(query_embedding, min(3, len(documents)))

    # Stage 4: Build context from retrieved documents
    # ------------------------------------------------------------
    relevant_docs = []
    context_parts = []

    for score, idx in zip(scores[0], indices[0]):
        if idx < len(documents):
            doc_info = {
                "content": documents[idx],
                "filename": filenames[idx],
                "score": float(score),
            }
            relevant_docs.append(doc_info)
            context_parts.append(f"[{doc_info['filename']}]\n{doc_info['content']}")

    if not relevant_docs:
        return "No relevant documents found for the query."

    # Combine context
    context = "\n\n".join(context_parts)

    # Stage 5: Augment by running the LLM to generate an answer
    # ------------------------------------------------------------
    llm_prompt = f"""Answer the question based on the provided context documents.

    Context:
    {context}

    Question: {prompt}

    Instructions:
    - Answer based only on the information in the context
    - Answer should beat least 10 words at max 20 words
    - If the context doesn't contain enough information, say so
    - Mention which document(s) you're referencing
    - Start with According to [document name]
    - Add brackets to the document name


    Answer:"""

    try:
        # Generate answer using Together AI
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[{"role": "user", "content": llm_prompt}],
            max_tokens=500,
            temperature=0.7,
        )
        answer = response.choices[0].message.content

        # Display source information
        print(f"\n📚 Most relevant source:")
        for doc in relevant_docs:
            print(f"  • {doc['filename']} (similarity: {doc['score']:.3f})")

        # Add source information to the answer
        sources_list = [doc["filename"] for doc in relevant_docs]
        sources_text = sources_list[0]
        full_answer = f"{answer}\n\n📄 Source Used: {sources_text}"

        return full_answer

    except Exception as e:
        return f"Error generating answer: {str(e)}"


if __name__ == "__main__":

    # Load dataset
    data_dict = {
        "project_kickoff": "Team discussed the launch of Project Phoenix. Key decisions made: using React for frontend, Node.js for backend, and MongoDB for database. Timeline set for 3 months with bi-weekly sprints. Team members assigned roles and responsibilities.",
        "bug_fix_meeting": "Emergency meeting to address critical security vulnerability in authentication system. Team identified root cause in JWT token validation. Immediate fix deployed to production. Post-mortem scheduled for tomorrow to prevent similar issues.",
        "design_review": "UX team presented new dashboard mockups. Feedback received on color scheme and navigation flow. Team agreed on dark mode implementation and simplified menu structure. Next iteration due in 2 weeks.",
        "client_feedback": "Client reported issues with PDF export functionality. Team investigated and found memory leak in PDF generation process. Temporary workaround implemented while permanent fix is being developed. Client satisfied with quick response.",
        "team_retrospective": "Monthly retrospective meeting held. Team celebrated successful deployment of new features. Areas for improvement identified: documentation needs updating, test coverage could be better. Action items assigned for next sprint.",
        "infrastructure_update": "DevOps team announced migration to new cloud provider. Timeline shared: 2 weeks for preparation, 1 week for migration, 1 week for testing. Team members assigned specific responsibilities for smooth transition.",
        "feature_planning": "Product team presented roadmap for Q3. New features planned: real-time collaboration, advanced analytics, and mobile app. Team discussed technical feasibility and resource requirements. Development to start next month.",
        "performance_review": "Quarterly performance review meeting. Team members shared achievements and challenges. Training needs identified: cloud architecture and security best practices. Budget approved for team certifications.",
        "integration_discussion": "Meeting with third-party API provider. Integration requirements discussed: OAuth2 authentication, rate limiting, and error handling. Technical documentation shared. Integration testing to begin next week.",
        "release_planning": "Release 2.0 planning session. Features finalized: user roles, audit logging, and API versioning. Release date set for end of month. Team created detailed deployment checklist and rollback plan."
    }

    question = "What are the issues our clients are having?"
    answer = run_rag(data_dict, question)
    print(f"\n🤖 Answer: {answer}\n")
    print("-" * 50)