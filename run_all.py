import subprocess

services = [
    ["python", "-m", "uvicorn", "clientes:app", "--reload", "--port", "8000"],
    ["python", "-m", "uvicorn", "productos:app", "--reload", "--port", "8001"],
    ["python", "-m", "uvicorn", "pedidos:app", "--reload", "--port", "8002"],
    ["python", "-m", "uvicorn", "inventario:app", "--reload", "--port", "8003"],
]

processes = []

for service in services:
    processes.append(subprocess.Popen(service))

for p in processes:
    p.wait()