from typing import Protocol

from .models import Account, ChatAnswer, Role
from .storage import Store


class BiometricClassifier(Protocol):
    def identify(self, modality: str, sample: bytes) -> str | None:
        """Return an enrolled account ID if the sample matches."""
        ...


class Authentication:
    def __init__(self, store: Store, classifier: BiometricClassifier):
        self.store = store
        self.classifier = classifier

    def sign_in(self, modality: str, sample: bytes) -> Account:
        if modality not in {"face", "voice"} or not sample:
            raise ValueError("Provide a face or voice sample.")
        account_id = self.classifier.identify(modality, sample)
        account = self.store.accounts.get(account_id) if account_id else None
        if account is None or account.suspended or account.role is Role.VISITOR:
            raise PermissionError("Sign-in failed.")
        return account


class ChatProvider(Protocol):
    def authorize(self, role: Role, question: str) -> None:
        """Reject requests for information outside the role's permissions."""
        ...

    def retrieve(self, role: Role, question: str) -> str | None:
        """Return an answer from permitted local material when relevant."""
        ...

    def generate(self, role: Role, question: str) -> str:
        """Answer a general question through an LLM."""
        ...


class Chat:
    def __init__(self, provider: ChatProvider):
        self.provider = provider

    def answer(self, role: Role, question: str) -> ChatAnswer:
        question = question.strip()
        if not question:
            raise ValueError("Enter a question.")
        self.provider.authorize(role, question)
        local_answer = self.provider.retrieve(role, question)
        if local_answer is not None:
            return ChatAnswer(local_answer, "RAG")
        return ChatAnswer(self.provider.generate(role, question), "LLM")


def run_creative_feature(account: Account | None, query: str) -> str:
    raise NotImplementedError("Add the team's creative feature here.")

