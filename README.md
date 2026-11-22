# CS-332-Project-JWD-
AI-powered smart bookstore featuring personalized book recommendations, multimodal book search, facial and voice authentication, and a RAG-based chatbot powered by local LLMs. Includes role-based access control, book purchasing, reviews, and customer management.

## Run the bookstore

From the repository root with Python 3.10+, download the catalog once and launch the app.

```powershell
python -m bookstore --sync-gutenberg
python -m bookstore
```

The desktop catalog uses ebook metadata from [Project Gutenberg](https://www.gutenberg.org/ebooks/offline_catalogs.html). Search and browse use the downloaded file offline. Select a book and use **Open free ebook** to visit its Gutenberg page. The year filter uses the Gutenberg ebook release year. To refresh the local copy, run the sync command again. You can also download the catalog CSV from Gutenberg’s offline catalogs page and save it as `pg_catalog.csv` in the repository root.

For the temporary checkout demo, run `python -m bookstore --demo`. Use `--list-books` with either catalog mode to print its contents in the terminal.
| File | Starting point |
| --- | --- |
| `models.py` and `storage.py` | Shared records, sample data, and seam for durable storage |
| `catalog.py` | Browse, keyword search, recommendations, book entry, and image search seam |
| `accounts.py` | Deposits, demo purchases, fines, VIP promotion, and account reopening |
| `reviews.py` | Ratings, purchaser weighting, taboo terms, warnings, and order status |
| `integrations.py` | Biometric classifier and role-aware RAG/LLM interfaces, plus creative-feature entry point |
| `__main__.py` and `desktop.py` | Terminal commands and desktop interface |
| `gutenberg.py` | Download and parse the official catalog |

The desktop app supports catalog search and browsing. Checkout is available in demo mode. The remaining
services can be called from Python while their screens are being built.
The biometric classifier, image search, chat provider, and creative feature
need implementations. Before using real accounts, add durable storage and
checkout transaction handling. Draft policies in this scaffold include
doubling verified purchaser weight and applying VIP demotion at three warnings.
