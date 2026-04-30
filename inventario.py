from fastapi import FastAPI, HTTPException
from typing import List
import csv
import json
import os
import pika
import requests
import threading

from datosCent import Inventario, InventarioRegistro, InventarioUpdate, bd_inventario

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

app = FastAPI(
    title="API de Inventario",
    description="Este es el servicio encargado de llevar el inventario de los productos de la empresa. \n\n"
    "Esta api actua como almacenamiento id y de la cantidad de los productos que hay en existencia. \n\n"
    "Ejecutar en puerto 8003 y los demas servicios en su respectivo puerto tal como: Clientes (8000), Pedidos (8002) y Productos (8001)",
    version="2.4.0",
    contact={
        "name": "Efren Camilo Jimenez Suarez ISC, Tecnm Queretaro",
    },
)


def consumir_pedidos():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue="pedidos", durable=True)

        def callback(ch, method, properties, body):
            mensaje = json.loads(body)

            if mensaje.get("evento") != "pedido_creado":
                return

            data = mensaje["data"]
            id_producto = data["id_producto"]
            cantidad = data["cantidad"]

            item = next((i for i in bd_inventario if i.id_producto == id_producto), None)
            if item is None:
                print("Producto no existe en inventario")
                return

            if item.cantidad < cantidad:
                print("Stock insuficiente")
                return

            item.cantidad -= cantidad
            guardar_inventarios(bd_inventario)
            print(f"Stock actualizado: {item.cantidad}")

        channel.basic_consume(
            queue="pedidos",
            on_message_callback=callback,
            auto_ack=True,
        )
        print("Inventario escuchando pedidos...")
        channel.start_consuming()
    except Exception as e:
        print("Error en consumidor:", e)


puerto_productos = os.getenv("PRODUCTOS_URL", "http://127.0.0.1:8001")

FILE_NAME = "inventario.csv"
HEADERS = ["id_producto", "cantidad"]

if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(HEADERS)


@app.get("/inventario", response_model=List[Inventario])
def obtener_productos():
    return bd_inventario


def guardar_inventarios(inventarios: List[Inventario]):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write("id_producto,cantidad\n")
        for c in inventarios:
            f.write(f"{c.id_producto},{c.cantidad}\n")


@app.post("/inventario")
def registrar_inventario(nuevo_registro: Inventario):
    try:
        respuesta = requests.get(f"{puerto_productos}/productos")
        if respuesta.status_code != 200:
            raise HTTPException(
                status_code=503,
                detail="El servicio de Productos respondio con error.",
            )

        productos = respuesta.json()
        existe_producto = any(p["id_producto"] == nuevo_registro.id_producto for p in productos)
        if not existe_producto:
            raise HTTPException(
                status_code=404,
                detail="Error: El producto no existe en el catalogo.",
            )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="El servicio de Productos no responde.",
        )

    for item in bd_inventario:
        if item.id_producto == nuevo_registro.id_producto:
            raise HTTPException(
                status_code=400,
                detail="Error: Ya existe inventario para este producto.",
            )

    bd_inventario.append(nuevo_registro)
    guardar_inventarios(bd_inventario)
    return {"mensaje": "Stock inicial registrado"}


@app.put("/inventario/descontar/{id_producto}")
def descontar_stock(id_producto: int, orden: InventarioRegistro):
    item = next((i for i in bd_inventario if i.id_producto == id_producto), None)

    if item is None:
        raise HTTPException(status_code=404, detail="El producto no tiene stock registrado.")

    if item.cantidad < orden.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Quedan {item.cantidad}.",
        )

    item.cantidad = item.cantidad - orden.cantidad
    guardar_inventarios(bd_inventario)

    return {
        "mensaje": "Stock actualizado tras descuento",
        "stock_restante": item.cantidad,
    }


@app.patch("/inventario/{id_producto}")
def actualizar_inventario(id_producto: int, datos_nuevos: InventarioUpdate):
    item_actual = next((i for i in bd_inventario if i.id_producto == id_producto), None)

    if item_actual is None:
        raise HTTPException(
            status_code=404,
            detail=f"No hay inventario registrado para el producto {id_producto}",
        )

    if datos_nuevos.cantidad is not None:
        item_actual.cantidad = datos_nuevos.cantidad

    guardar_inventarios(bd_inventario)
    return {"mensaje": "Stock actualizado correctamente", "datos": item_actual}


@app.on_event("startup")
def iniciar_consumidor():
    hilo = threading.Thread(target=consumir_pedidos, daemon=True)
    hilo.start()
