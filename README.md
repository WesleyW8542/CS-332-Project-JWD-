# CS-332-Project-JWD-
AI-powered smart bookstore featuring personalized book recommendations, multimodal book search, facial and voice authentication, and a RAG-based chatbot powered by local LLMs. Includes role-based access control, book purchasing, reviews, and customer management.

## Run the coding scaffold

Run these from the repository root with Python 3.10+.

```powershell
python -m bookstore
python -m bookstore --list-books
```

The first command opens the Tkinter desktop prototype. The second lists the
sample catalog in a terminal. The GUI starts with a demo customer and a $12
balance. Search for a book, then select it and try checkout. Demo data resets
each time the app starts.

| File | Starting point |
| --- | --- |
| `models.py` and `storage.py` | Shared records, sample data, and seam for durable storage |
| `catalog.py` | Browse, keyword search, recommendations, book entry, and image search seam |
| `accounts.py` | Deposits, demo purchases, fines, VIP promotion, and account reopening |
| `reviews.py` | Ratings, purchaser weighting, taboo terms, warnings, and order status |
| `integrations.py` | Biometric classifier and role-aware RAG/LLM interfaces, plus creative-feature entry point |
| `__main__.py` | Desktop prototype and terminal catalog entry point |

The desktop prototype connects catalog search and checkout. The remaining
services can be called from Python while their screens are being built.
The biometric classifier, image search, chat provider, and creative feature
need implementations. Before using real accounts, add durable storage and
checkout transaction handling. Draft policies in this scaffold include
doubling verified purchaser weight and applying VIP demotion at three warnings.
