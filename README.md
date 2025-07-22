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
  │
  ├── 📂 recurser-ui/
  │   ├── 📄 Dockerfile
  │   ├── 📄 requirements.txt
  │   ├── 📄 recurser\_app.py
  │   └── 📂 .streamlit/
  │       ├── 📄 config.dev.toml
  │       └── 📄 config.prod.toml
  │   
  └── 📂 ollama/
      ├── 📄 Dockerfile
```

---

## 🐳 **Docker commands**

✅ **Build the images**

```bash
docker compose build
```

```bash
docker compose build llm
```

✅ **Run the containers**

```bash
docker compose up
```

✅ **Stop the containers**

```bash
docker compose down
```

✅ **See what containers are running**

```bash
docker ps
```

✅ **Enter the Python container**

```bash
docker compose exec gigaclass bash
```

---

## ⚡ **Development tips**

* Your Python files are bind-mounted inside the container, so **code changes appear immediately**.
* If you use **VS Code**, the recommended way is to work inside a **Dev Container** so your linter and Python environment match the container.

---

## 🧑‍💻 **VS Code Dev Containers**

1. Open VS Code.
2. Press **Ctrl+Shift+P** (or Cmd+Shift+P on Mac).
3. Run **“Dev Containers: Attach to Running Container…”**.
4. Pick the Python container (`gigaclass`).
5. Press **Ctrl+Shift+P** again → run **“Dev Containers: Open Folder in Container…”** → choose `/app/`.
6. Now your linter, autocompletion, and terminal all match your container environment.

✅ This way, you don’t need to install packages locally, they’re inside the container.

---

## ✅ **Quick notes**

* By default, the Streamlit app runs on **[http://localhost:8501](http://localhost:8501)**.
* The ChromaDB container runs in the same Docker network — your Python code connects to it using the hostname `chromadb`.
* The `config.dev.toml` enables **hot reload** for Streamlit while developing.
* To disable hot reload and set production settings, switch to `config.prod.toml` in your `docker-compose.yml`.

---

## 🗝️ **Troubleshooting**

* If you change your `Dockerfile` or `requirements.txt`, always rebuild with:

  ```bash
  docker compose build
  ```
* To reset your database, run:

  ```bash
  docker compose down -v
  ```

---

## ❤️ **Happy coding!**

Feel free to fork and adapt, this is a solid base for building a Python data app with a database in a reproducible Docker environment.
