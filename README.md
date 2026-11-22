# CS-332-Project-JWD-
AI-powered smart bookstore featuring personalized book recommendations, multimodal book search, facial and voice authentication, and a RAG-based chatbot powered by local LLMs. Includes role-based access control, book purchasing, reviews, and customer management.

## Run the bookstore

Install Python 3.10 or newer. After cloning or pulling the project, open PowerShell in the repository root.

### First launch on each computer

```powershell
python -m bookstore --sync-gutenberg
python -m bookstore
```

The sync command needs an internet connection and saves `pg_catalog.csv` on your computer. Git ignores this file, so each teammate downloads it once. Everyone running the same code gets the same app features. The exact titles and counts can vary if Project Gutenberg updates its catalog between downloads. [Project Gutenberg offline catalogs](https://www.gutenberg.org/ebooks/offline_catalogs.html)

### Later launches

Run `python -m bookstore` to reuse your local catalog. Search and browse work offline. The year filter uses the Gutenberg ebook release year, and **Open free ebook** opens the title’s page in your browser. Run the sync command again whenever you want to refresh the catalog.

### Checkout demo

Run `python -m bookstore --demo` for the same four sample books and a fresh $12 demo balance each time. This mode works without a catalog download. Add `--list-books` to either launch command to list books in the terminal.

## Code guide

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
