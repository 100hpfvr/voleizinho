# run_streamlit.py
import subprocess

subprocess.run([
    "streamlit",
    "run",
    "app.py",         # ou o nome do seu script principal
    "--server.port", "2000"
])