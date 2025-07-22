

## **1. Build the Docker Image (if you haven’t already or after code changes)**
```powershell
docker build -t dynamicfilerouting .
```

---Step 2: Run This Command Inside the Cursor Terminal : docker exec -it vibrant_chatelet bash

## **2. Start a New Container with Your Project Mounted and a Shell** 

This command will: 
- Mount your entire project (including `agents`) into `/workspace` in the container.
- Start a bash shell so you can run any commands you want inside the container.

```powershell
docker run -it -v ${PWD}:/workspace dynamicfilerouting /bin/bash
```
> If `${PWD}` does not work in PowerShell, use:
> ```powershell
> docker run -it -v (Get-Location):/workspace dynamicfilerouting /bin/bash
> ```

---

## **3. Once Inside the Container**

You’ll see a prompt like `root@...:/workspace#`.  
Now you can run:
```sh
ls
python main_OAIAgentic.py
```
and you should see the `agents` directory and all your project files.

---

## **4. (Optional) If You Want to Run the Script Directly (No Shell)** -->** below will run without opening container.

You can run your script directly (without a shell) with:
```powershell
docker run -it -v ${PWD}:/workspace dynamicfilerouting
```
This will use the default command in your Dockerfile (`python main_OAIAgentic.py`).

---

## **Summary Table**

| Action                        | Command                                                                 |
|-------------------------------|-------------------------------------------------------------------------|
| Build image                   | `docker build -t dynamicfilerouting .`                                  |
| Start container with shell    | `docker run -it -v ${PWD}:/workspace dynamicfilerouting /bin/bash`      |
| (PowerShell alt)              | `docker run -it -v (Get-Location):/workspace dynamicfilerouting /bin/bash` |
| Run script directly           | `docker run -it -v ${PWD}:/workspace dynamicfilerouting`                |

---

**Use the shell method if you want to explore, debug, or run multiple commands.  
Use the direct run if you just want to execute your script.**

#####
If you mount your local root directory (-v ${PWD}:/workspace) when running the container, any changes you make to your local files (add scripts, edit code, etc.) are instantly reflected inside the running container.
You only need to rebuild the Docker image if you change dependencies (e.g., requirements.txt, setup.py, or the Dockerfile itself).
**---## **Typical Scenarios**
### **A. You Add/Edit Scripts or Data Files in Your Local Project** - **No need to rebuild the image!** - Just run the container with the volume mount as before: ``powershell
docker run -it -v ${PWD}:/workspace dynamicfilerouting /bin/bash