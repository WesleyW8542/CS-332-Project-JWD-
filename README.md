# CS-332-Project-JWD-
Desktop bookstore with Project Gutenberg titles, keyword and image search, personalized recommendations, voice sign-in, checkout, and reviews. Ollama chat and retrieval are planned.

## Run the bookstore

Install Python 3.10 or newer. After cloning or pulling the project, open PowerShell in the repository root.

### First launch on each computer

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m bookstore --sync-gutenberg
.\.venv\Scripts\python.exe -m bookstore
```

The sync command needs an internet connection and saves `pg_catalog.csv` on your computer. Git ignores this file, so each teammate downloads it once. Everyone running the same code gets the same app features. The exact titles and counts can vary if Project Gutenberg updates its catalog between downloads. [Project Gutenberg offline catalogs](https://www.gutenberg.org/ebooks/offline_catalogs.html)

### Later launches

Run `.\.venv\Scripts\python.exe -m bookstore` to reuse your local catalog. The shorter `python` commands below assume you have activated the environment or selected it in VS Code. Search and browse work offline. The year filter uses the ebook release year for Gutenberg titles and the publication year for locally added books. **Open free ebook** opens the title’s page in your browser. Run the sync command again whenever you want to refresh the catalog.

### Sign in and register

The specification calls for biometric sign-in for registered customers, VIPs, and super-users. This prototype uses a voice sample. Visitors can browse without signing in. In the main app, click **Register** to record three short samples of the displayed phrase, then **Sign in** to record another sample. Use the same microphone and speak clearly. Registration starts a customer with a $0 balance. For a local super-user, the computer operator can run `python -m bookstore --provision-admin USERNAME` and record three samples, then sign in from the desktop. Voice matching is a course prototype and has no replay detection.

The main app saves account balances, purchase receipts, recommendations, ratings, warnings, voice features, and store/team notes locally in `bookstore_activity.sqlite3`. Demo account activity resets each time.

### Image search and reviews

Use **Search by image** to select a JPEG or PNG. Text in the search box narrows the image matches. An SU can attach a searchable cover in **Add book**. For Gutenberg covers or interior images, put reference files under `book_images/` with names such as `PG-84.jpg` or `PG-84__figure.png`, using the ebook ID from its Gutenberg page. Image search covers the entries for which you have reference images.

Select a book for **Ratings and reviews** or **Find similar books**. Anyone can read reviews. Only a signed-in registered customer or VIP can post one, and only once per title. Super-users can edit **Prohibited words**, inspect **Order lists**, or update **Store and team info**. **My account** shows the balance, warnings, and purchase history.

### Recommendations

Select a book in the catalog to record a view, then click **Recommendations** to refresh the top three. Customers and VIPs get results based on their own views and purchases. Visitors and super-users get results based on overall activity in the local catalog. The main app saves activity across launches. Demo activity is session-only.

### Customer checkout demos

Open `python -m bookstore` to browse Gutenberg as a visitor. To try checkout, use one of these demo modes.

| Role | Launch command |
| --- | --- |
| Registered customer | `python -m bookstore --demo` |
| VIP customer | `python -m bookstore --demo-vip` |

Both demos start with the same four sample books and a fresh $12 balance without a Gutenberg download. The VIP demo shows and applies a 10% discount. For example, an $8.00 book costs $7.20. Add `--list-books` to a launch command to list the books in the terminal.

Click **Add funds** to make a demo deposit. If you confirm a purchase above your balance, the app charges the purchase price plus a $1 fine and suspends the resulting negative account.

### Super-user demo

```powershell
python -m bookstore --demo-admin
```

1. Click **Add book**.
2. Enter a title, author, category, publication year, and price in dollars, such as `9.50`.
3. Click **Save book**. The app displays the new entry, and you can find it using search or browse.

This mode opens with a demo super-user for testing the admin controls. The **Add book** button is available to active super-users. Books you save are stored in `local_catalog.sqlite3` and appear on later launches in super-user demo mode and in the main catalog. Git ignores this database, so each computer keeps its own additions.

To try reopening an account, click **Reopen account**, enter `demo-suspended`, and deposit more than $0.50. This demo account starts at −$0.50. Account balances and status reset when the app closes.

## Run the tests

```powershell
python -m unittest discover -s tests -t .
```

The tests cover checkout, fines, VIP pricing and promotion, reopening, reviews and warnings, order lists, recommendations, and the SQLite activity store. They use only the standard library and do not need a microphone, Gutenberg download, or display.

## Code guide

| File | Starting point |
| --- | --- |
| `models.py` and `storage.py` | Shared records, sample data, and SQLite storage for added books |
| `catalog.py` | Browse, keyword search, recommendations, book entry, and combined keyword and image search |
| `account_ui.py` | Desktop account summary, deposits, and reopening |
| `accounts.py` | Deposits, purchases, fines, VIP promotion, and account reopening |
| `reviews.py` | Ratings, purchaser weighting, taboo terms, warnings, and order status |
| `integrations.py` | Authentication and role-aware RAG/LLM interfaces |
| `__main__.py` and `desktop.py` | Terminal commands and desktop interface |
| `admin.py` | Super-user book entry, cover attachment, and store/team information |
| `activity.py` | Transactional local account and activity storage |
| `auth_ui.py` and `voice.py` | Microphone enrollment and voice matching |
| `image_search.py` | Matching against stored covers and interior images |
| `review_ui.py` | Ratings, reviews, prohibited words, and order lists |
| `gutenberg.py` | Download and parse the official catalog |

The chatbot and Ollama/RAG integration are pending. The [Phase II design report](Phase-II-Design-Report.md) maps workflows to the team’s diagrams.
