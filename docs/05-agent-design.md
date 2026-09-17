# Agent Design & LLM Abstraction

## 1. LangGraph State Workflow
The matching and document generation pipeline operates as a stateful graph in LangGraph:

```text
[ Load Job & Profile State ]
           │
           ▼
[ Deterministic Criteria Node ] ──► (Disqualified if fails hard filters)
           │
           ▼
[ Vector Similarity Node ] ────────► (Disqualified if score < threshold)
           │
           ▼
[ LLM Skill Gap Analysis Node ]
           │
           ▼
[ Grounded Document Generation Node ]
           │
           ▼
[ Anti-Hallucination Guardrail Node ]
           │
           ▼
[ Human Review Interrupt / Approval ]
```

## 2. Provider Abstraction Design

All agent nodes interact with LLMs using a uniform provider interface:

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, temperature: float = 0.2) -> str:
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Type[T], temperature: float = 0.0) -> T:
        pass
```

Concrete implementations:
- `GeminiProvider` (Google Gemini API)
- `GroqProvider` (Groq API)
- `MistralProvider` (Mistral AI API)

Provider factory selects active instance from `ACTIVE_LLM_PROVIDER` in settings.
