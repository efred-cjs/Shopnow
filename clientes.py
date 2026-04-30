from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List
from jose import JWTError, jwt
import csv
import json
import os
import pika

from datosCent import Cliente, ClienteRegistro, ClienteUpdate, bd_clientes

SECRET_KEY = "tu_llave_secreta_super_segura_123"
ALGORITHM = "HS256"
security = HTTPBearer()
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

FILE_NAME = "clientes.csv"
HEADERS = ["id_cliente", "nombre", "correo", "direccion", "telefono"]

if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(HEADERS)


def crear_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")


app = FastAPI(
    title="API de Clientes",
    description="Este es el servicio encargado del registro basico inicial de los clientes. \n\n"
    "Esta api actua como eje de nuestro programa para el seguimiento y modificacion de los clientes. \n\n"
    "Ejecutar en puerto 8000 y los demas servicios en su respectivo puerto tal como: Pedidos (8002) y Productos (8001)",
    version="2.2.1",
    contact={
        "name": "Efren Camilo Jimenez Suarez ISC, Tecnm Queretaro",
    },
)


def enviar_evento(tipo_evento, data):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue="clientes", durable=True)

        mensaje = {
            "evento": tipo_evento,
            "data": data,
        }

        channel.basic_publish(
            exchange="",
            routing_key="clientes",
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
    except Exception as e:
        print("Error enviando a RabbitMQ:", e)


@app.get("/clientes", response_model=List[Cliente])
def obtener_clientes():
    return bd_clientes


@app.get("/clientes_seguro", response_model=List[Cliente])
def obtener_clientes_seguro(token_data=Depends(verificar_token)):
    return bd_clientes


def guardar_clientes(clientes: List[Cliente]):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write("id_cliente,nombre,correo,direccion,telefono\n")
        for c in clientes:
            f.write(f"{c.id_cliente},{c.nombre},{c.correo},{c.direccion},{c.telefono}\n")


@app.post("/clientes")
def registrar_cliente(nuevo_cliente: ClienteRegistro):
    nuevo_id = 1 if len(bd_clientes) == 0 else max(c.id_cliente for c in bd_clientes) + 1

    cliente = Cliente(
        id_cliente=nuevo_id,
        nombre=nuevo_cliente.nombre,
        correo=nuevo_cliente.correo,
        direccion=nuevo_cliente.direccion,
        telefono=int(nuevo_cliente.telefono),
    )

    bd_clientes.append(cliente)
    guardar_clientes(bd_clientes)
    enviar_evento("cliente_creado", cliente.dict())

    return {"Alerta": "Cliente registrado exitosamente", "id": nuevo_id}


@app.post("/login", tags=["Autenticacion"])
def login(nombre: str, telefono: str):
    cliente = next((c for c in bd_clientes if c.nombre == nombre), None)

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if str(cliente.telefono) != telefono:
        raise HTTPException(status_code=401, detail="Telefono incorrecto")

    token = crear_token({"usuario": cliente.nombre})
    return {"token": token, "mensaje": "Logueado con exito"}


@app.delete("/clientes/{id_cliente}")
def eliminar_cliente(id_cliente: int):
    borrar_cliente = next((c for c in bd_clientes if c.id_cliente == id_cliente), None)
    if not borrar_cliente:
        raise HTTPException(status_code=404, detail=f"No se encontraron clientes con este ID {id_cliente}")

    bd_clientes.remove(borrar_cliente)
    guardar_clientes(bd_clientes)
    enviar_evento("cliente_eliminado", {"id_cliente": id_cliente})
    return {"Alerta": f"Cliente {id_cliente} eliminado exitosamente de la memoria"}


@app.patch("/clientes/{id_cliente}")
def actualizar_cliente(id_cliente: int, update_datos: ClienteUpdate):
    cliente_update = next((c for c in bd_clientes if c.id_cliente == id_cliente), None)

    if not cliente_update:
        raise HTTPException(status_code=404, detail=f"No se encontro el cliente con ID {id_cliente}")

    if update_datos.nombre is not None:
        cliente_update.nombre = update_datos.nombre
    if update_datos.correo is not None:
        cliente_update.correo = update_datos.correo
    if update_datos.direccion is not None:
        cliente_update.direccion = update_datos.direccion
    if update_datos.telefono is not None:
        cliente_update.telefono = update_datos.telefono

    guardar_clientes(bd_clientes)
    enviar_evento("cliente_actualizado", cliente_update.dict())
    return {"mensaje": "Cliente actualizado correctamente", "datos": cliente_update}
