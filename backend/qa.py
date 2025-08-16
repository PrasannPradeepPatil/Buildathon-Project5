import os
import re
from typing import List, Dict, Any, Optional
import openai
from backend.config import OPENAI_API_KEY
from backend.retrieval import RetrievalService
import os
from typing import Optional, Dict, Any, List
from backend.neo4j_store import Neo4jStore
from backend.graph_ops import GraphOperations

# Configure OpenAI if key is available
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

class QAService:
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval = retrieval_service
        self.use_llm = bool(OPENAI_API_KEY)

    def answer_question(self, question: str, k: int = 10) -> Dict[str, Any]:
        """Answer a question using retrieved context."""
        # Retrieve relevant chunks
        chunk_results = self.retrieval.search_chunks(question, k)

        if not chunk_results:
            return {
                'answer': "I couldn't find any relevant information to answer your question.",
                'sources': [],
                'nodes_used': []
            }

        # Expand context with related concepts
        expanded_context = self.retrieval.expand_context(chunk_results)

        # Generate answer
        if self.use_llm:
            answer_data = self._llm_answer(question, chunk_results)
        else:
            answer_data = self._extractive_answer(question, chunk_results)

        # Add concept nodes used
        concept_labels = [concept['label'] for concept in expanded_context.get('concepts', [])]
        answer_data['nodes_used'] = concept_labels[:10]  # Top 10 concepts

        return answer_data

    def _llm_answer(self, question: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate answer using LLM."""
        # Prepare context
        context_snippets = self.retrieval.select_best_snippets(chunks, max_snippets=5)
        context = '\n\n'.join(f"[{i+1}] {snippet}" for i, snippet in enumerate(context_snippets))

        # Truncate context to ~500 tokens (rough estimate)
        if len(context) > 2000:
            context = context[:2000] + "..."

        system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
        Always cite your sources using the numbered references [1], [2], etc. 
        Keep your answer concise and factual. If you cannot answer based on the context, say so."""

        user_prompt = f"""Question: {question}

        Context:
        {context}

        Please provide a concise answer with citations."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )

            answer = response.choices[0].message.content.strip()

        except Exception as e:
            # Fallback to extractive if LLM fails
            return self._extractive_answer(question, chunks)

        # Prepare sources
        sources = []
        for i, chunk in enumerate(chunks[:5]):
            sources.append({
                'docId': chunk.get('doc_id', ''),
                'snippet': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                'url': None,  # Will be filled by caller if available
                'score': chunk.get('normalized_score', chunk.get('combined_score', 0))
            })

        return {
            'answer': answer,
            'sources': sources
        }

    def _extractive_answer(self, question: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate extractive answer from chunks."""
        # Simple extractive approach: select top sentences
        all_sentences = []

        for chunk in chunks[:5]:  # Top 5 chunks
            text = chunk['text']
            # Simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20:  # Avoid very short sentences
                    all_sentences.append({
                        'text': sentence,
                        'score': chunk.get('normalized_score', chunk.get('combined_score', 0)),
                        'docId': chunk.get('doc_id', ''),
                        'chunk_text': text
                    })

        # Sort by score and take top 3-4 sentences
        all_sentences.sort(key=lambda x: x['score'], reverse=True)
        top_sentences = all_sentences[:4]

        # Combine into answer
        answer = '. '.join(sentence['text'] for sentence in top_sentences)
        if answer and not answer.endswith('.'):
            answer += '.'

        # Prepare sources
        sources = []
        seen_docs = set()

        for sentence in top_sentences:
            doc_id = sentence['docId']
            if doc_id not in seen_docs:
                sources.append({
                    'docId': doc_id,
                    'snippet': sentence['chunk_text'][:200] + '...' if len(sentence['chunk_text']) > 200 else sentence['chunk_text'],
                    'url': None,
                    'score': sentence['score']
                })
                seen_docs.add(doc_id)

        return {
            'answer': answer or "I couldn't generate a clear answer from the available information.",
            'sources': sources
        }

class QAEngine:
    """Question answering engine using the knowledge graph."""

    def __init__(self, neo4j_store: Neo4jStore, graph_ops: GraphOperations):
        self.store = neo4j_store
        self.graph_ops = graph_ops

    async def answer_question(self, question: str, k: int = 10) -> Dict[str, Any]:
        """Answer a question using the knowledge graph."""
        try:
            # Search for relevant content
            search_results = await self.search(question, k)

            # Extract relevant nodes (simplified approach)
            relevant_nodes = []
            question_lower = question.lower()

            # Get stats to check if we have real data
            stats = await self.store.get_statistics()
            if stats.get('chunks', 0) > 0:
                # We have real data, try to find relevant concepts
                # This is a simplified implementation
                if any(word in question_lower for word in ['machine', 'ml', 'learning']):
                    relevant_nodes.append('Machine Learning')
                if any(word in question_lower for word in ['python', 'programming', 'code']):
                    relevant_nodes.append('Python')
                if any(word in question_lower for word in ['data', 'science', 'analysis']):
                    relevant_nodes.append('Data Science')

            # Generate answer based on search results
            sources = search_results.get('results', [])
            if sources:
                answer = f"Based on the available documents, here's what I found about '{question}': "
                answer += " ".join([result.get('text', '')[:200] + "..." for result in sources[:2]])
            else:
                answer = f"I couldn't find specific information about '{question}' in the current knowledge base."

            return {
                "answer": answer,
                "sources": [
                    {
                        "snippet": result.get('text', '')[:300] + "...",
                        "score": result.get('score', 0.0),
                        "docId": result.get('doc_id', ''),
                        "doc_name": f"Document {result.get('doc_id', 'Unknown')}",
                        "url": result.get('url', '')
                    } for result in sources[:3]
                ],
                "nodes_used": relevant_nodes or ['General Knowledge']
            }

        except Exception as e:
            return {
                "answer": f"Sorry, I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "nodes_used": [],
                "error": str(e)
            }

    async def search(self, query: str, k: int = 10) -> Dict[str, Any]:
        """Search for relevant content."""
        try:
            # This would normally use vector search
            # For now, return a simple implementation
            return {
                "query": query,
                "results": [
                    {
                        "chunk_id": "sample_chunk_1",
                        "text": f"Sample content related to '{query}'",
                        "doc_id": "sample_doc_1",
                        "score": 0.85
                    }
                ]
            }
        except Exception as e:
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }