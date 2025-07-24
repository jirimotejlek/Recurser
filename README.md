# 🚀 Recurser
Recursive Search Engine

This is a **minimal starter project** that shows how to run a **Streamlit Python web app** with a **ChromaDB** database using Docker containers.

It supports **hot reload** for rapid development and works well with **VS Code Dev Containers**.

---

## 📂 Project structure

```
project-root/
  │
  ├── 📄 docker-compose.yml
  ├── 📄 docker-compose.base.yml
  ├── 📄 docker-compose.local.yml
  ├── 📄 docker-compose.external.yml
  ├── 📄 recurser.sh (macOS/Linux)
  ├── 📄 recurser (Windows)
  │
  ├── 📂 env-templates/
  │   ├── 📄 openai
  │   ├── 📄 anthropic
  │   ├── 📄 mistral
  │   └── 📄 custom
  │
  ├── 📂 recurser-ui/
  │   ├── 📄 Dockerfile
  │   ├── 📄 requirements.txt
  │   ├── 📄 recurser_app.py
  │   └── 📂 .streamlit/
  │       ├── 📄 config.dev.toml
  │       └── 📄 config.prod.toml
  │  
  └── 📂 ollama/
      ├── 📄 Dockerfile
```

---

## 🧠 External vs Local LLM

You can use this project with a **local LLM** (via Ollama) or connect it to an **external API** (OpenAI, Anthropic, etc.).

### 🏠 Local LLM (Default)

```bash
# macOS/Linux
./recurser.sh run-local

# Windows
recurser run-local
```

### 🌐 External LLM Provider

```bash
# 1. Copy a provider template
cp env-templates/openai .env

# 2. Edit .env and add your API key
nano .env  # or any text editor

# 3. Run with external provider
# macOS/Linux
./recurser.sh run-external

# Windows
recurser run-external
```

The flow is like this:
```text
.env file (from env-templates/)
    ↓
docker-compose.external.yml reads .env
    ↓
Container environment variables
```

---

## 🐳 Docker Commands

We provide a single management script for all Docker operations:

### macOS/Linux

```bash
# First time setup - make script executable
chmod +x recurser.sh

# Build containers
./recurser.sh build-local      # For local LLM
./recurser.sh build-external   # For external LLM

# Run services
./recurser.sh run-local        # Start with local LLM
./recurser.sh run-external     # Start with external LLM

# Management
./recurser.sh status           # Check container status
./recurser.sh logs             # View all logs
./recurser.sh logs llm-dispatcher  # View specific service logs
./recurser.sh stop             # Stop services (containers preserved)
./recurser.sh restart          # Restart stopped services
./recurser.sh remove           # Remove project containers and volumes
./recurser.sh help             # Show all available commands

# Quick workflow
./recurser.sh run-local -d     # Start in background
./recurser.sh stop             # Stop when done (containers remain)
./recurser.sh restart          # Resume work later
```

### Windows

```batch
# Build containers
recurser build-local       # For local LLM
recurser build-external    # For external LLM

# Run services
recurser run-local         # Start with local LLM
recurser run-external      # Start with external LLM

# Management
recurser status            # Check container status
recurser logs              # View all logs
recurser logs llm-dispatcher   # View specific service logs
recurser stop              # Stop services (containers preserved)
recurser restart           # Restart stopped services
recurser remove            # Remove project containers and volumes
recurser help              # Show all available commands

# Quick workflow
recurser run-local -d      # Start in background
recurser stop              # Stop when done (containers remain)
recurser restart           # Resume work later
```

### 📋 Available Commands

- **`run-local`** - Start services with local LLM
- **`run-external`** - Start services with external LLM provider
- **`build-local`** - Build containers for local setup
- **`build-external`** - Build containers for external setup
- **`stop`** - Stop running services (containers are preserved)
- **`restart`** - Restart stopped services
- **`status`** - Show status of project containers
- **`logs`** - View logs (optionally specify service name)
- **`remove`** - Remove all project containers and volumes
- **`help`** - Show help message

---

## ⚡ Development tips

* Your Python files are bind-mounted inside the container, so **code changes appear immediately**.
* The scripts only rebuild containers when you explicitly use the `build-*` commands, making daily development faster.
* If you use **VS Code**, the recommended way is to work inside a **Dev Container** so your linter and Python environment match the container.

---

## 🧑‍💻 VS Code Dev Containers

1. Open VS Code.
2. Press **Ctrl+Shift+P** (or Cmd+Shift+P on Mac).
3. Run **"Dev Containers: Attach to Running Container…"**.
4. Pick the Python container (`recurser-ui`).
5. Press **Ctrl+Shift+P** again → run **"Dev Containers: Open Folder in Container…"** → choose `/app/`.
6. Now your linter, autocompletion, and terminal all match your container environment.

✅ This way, you don't need to install packages locally, they're inside the container.

---

## ✅ Quick notes

* By default, the Streamlit app runs on **[http://localhost:8501](http://localhost:8501)**.
* The ChromaDB container runs at **[http://localhost:8000](http://localhost:8000)**.
* The Ollama LLM (local mode) runs at **[http://localhost:11434](http://localhost:11434)**.
* All containers communicate via the Docker network — your Python code connects using hostnames like `chromadb` and `llm`.
* The `config.dev.toml` enables **hot reload** for Streamlit while developing.
* To disable hot reload and set production settings, switch to `config.prod.toml` in your `docker-compose.yml`.

---

## 🗝️ Troubleshooting

* If you change your `Dockerfile` or `requirements.txt`, always rebuild:
  ```bash
  # macOS/Linux
  ./recurser.sh build-local
  
  # Windows
  recurser build-local
  ```

* To stop services without removing containers:
  ```bash
  # macOS/Linux
  ./recurser.sh stop
  
  # Windows
  recurser stop
  ```

* To completely reset your database and start fresh:
  ```bash
  # macOS/Linux
  ./recurser.sh remove
  
  # Windows
  recurser remove
  ```

* To see what's running:
  ```bash
  # macOS/Linux
  ./recurser.sh status
  
  # Windows
  recurser status
  ```

---

## 🌍 Supported LLM Providers

### Local
- **Ollama** with Gemma model (default, no API costs)

### External
- **OpenAI** - GPT-4, GPT-3.5-turbo
- **Anthropic** - Claude 3 Opus, Sonnet
- **Mistral** - Mistral Large, Medium
- **Custom** - Any OpenAI-compatible API

See `env-templates/` for configuration examples.

---

## ❤️ Happy coding!

Feel free to fork and adapt, this is a solid base for building a Python data app with a database in a reproducible Docker environment.