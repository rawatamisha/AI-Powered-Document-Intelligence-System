import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chatbot.rag_chain import RAGChatbot
from src.retrieval.vector_store import DocumentVectorStore


def main() -> None:
    print("Enter your question (press Enter on an empty line to exit):")
    while True:
        question = input("Question: ").strip()
        if not question:
            break

        with DocumentVectorStore() as store:
            chatbot = RAGChatbot(vector_store=store)
            response = chatbot.answer(question)

        print("\nAnswer:")
        print(response.answer_text)
        print(f"\nCitations: {len(response.citations)}")
        print("-" * 60)


if __name__ == "__main__":
    main()
