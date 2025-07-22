
```markdown
# 📦 Dynamic File Routing with Docker

This project is a Python-based file processing pipeline that reads config from Excel, processes local SharePoint files, profiles data, formats output, and routes the final files to different destinations — all containerized with Docker.

---

## 🚀 Features

- Excel-based dynamic config routing
- Schema validation and column extraction
- Data profiling and CSV generation
- File routing to local S3/SP folders
- Dockerized for consistent dev environment

---

## 🧱 Project Structure

```

Project\_DynamicFileRouting/
├── .devcontainer/         # Dev Container support (Cursor/VS Code)
│   ├── devcontainer.json
│   └── Dockerfile
├── agents/                # Custom module (if applicable)
├── config/                # Input config Excel
├── local\_sharepoint/      # Simulated SharePoint folder
├── S3\_upload/             # Simulated S3 output
├── SP\_upload/             # Simulated SharePoint output
├── temp\_files/            # Temp storage for processed files
├── requirements.txt       # Python dependencies
├── main\_OAIAgentic.py     # Main script
├── .env                   # Environment variables
└── README.md

````

---

## 🧑‍💻 Local Development

### ✅ 1. Clone the Repo

```bash
git clone https://github.com/<your-username>/DynamicRouting_Docker.git
cd DynamicRouting_Docker
````

### ✅ 2. (Optional) Update `.env`

Set your environment variables (e.g., `ROOT_DIR`) in `.env`:

```env
ROOT_DIR=/workspace
```

> 💡 You may copy from `.env.example` if provided.

---

## 🐳 Docker Usage

### 🔧 1. Build the Image

```bash
docker build -t dynamicfilerouting .
```

### ▶️ 2. Run the Container

```bash
docker run -it --env-file .env dynamicfilerouting bash
```

Then run your script inside the container:

```bash
python main_OAIAgentic.py
```

### 📂 3. (Optional) Mount Volumes

To persist inputs/outputs:

```bash
docker run -it \
  --env-file .env \
  -v ${PWD}/config:/workspace/config \
  -v ${PWD}/local_sharepoint:/workspace/local_sharepoint \
  -v ${PWD}/S3_upload:/workspace/S3_upload \
  -v ${PWD}/SP_upload:/workspace/SP_upload \
  dynamicfilerouting bash
```

---

## 🧠 Dev Container Support (Cursor / VS Code)

If you're using [Cursor](https://www.cursor.so/) or VS Code:

1. Open the folder `Project_DynamicFileRouting`
2. Accept “Reopen in Container” prompt
3. Terminal inside container is pre-configured
4. Run:

```bash
python main_OAIAgentic.py
```

---

## 📦 Installing Dependencies (If Running Manually)

```bash
pip install -r requirements.txt
```

> If inside Docker container:
> `docker exec -it <container-name> pip install -r /workspace/requirements.txt`

---

## 🔁 Updating `requirements.txt`

To install new packages into a running container:

```bash
docker cp requirements.txt <container-name>:/workspace/
docker exec -it <container-name> pip install -r /workspace/requirements.txt
```

---

## 📤 Exporting Docker Image to Share

```bash
docker save -o dynamicfilerouting.tar dynamicfilerouting
# Recipient:
docker load -i dynamicfilerouting.tar
```

---

## 🧩 Troubleshooting

* `ModuleNotFoundError: No module named 'agents'`
  → Ensure `agents/` folder exists or is installed via pip

* `dict()` deprecation warning in Pydantic
  → Replace `input.dict()` with `input.model_dump()` or downgrade Pydantic to 1.10

---

## 📜 License

MIT License (or your preferred license)

---

## 🙋‍♀️ Contributions Welcome

PRs and issues are welcome! Fork the repo, improve the code, and open a pull request.

```
