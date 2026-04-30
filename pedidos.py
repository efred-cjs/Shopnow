from fastapi import FastAPI, HTTPException
from typing import List
import csv
import json
import os
import pika
import requests

from config import get_data_file, get_rabbitmq_connection_parameters, get_service_url
from datosCent import Pedido, PedidoUpdate, bd_pedidos

app = FastAPI(
    title="API de Pedidos",
    description="Este es el servicio encargado de llevar el registro de pedidos de la empresa. \n\n"
    "Esta api actua como almacenamiento de los pedidos sobre los productos que hay en existencia. \n\n"
    "Ejecutar en puerto 8002 y los demas servicios en su respectivo puerto tal como: Clientes (8000), Productos (8001) e Inventario (8003)",
    version="2.4.0",
    contact={
        "name": "Efren Camilo Jimenez Suarez ISC, Tecnm Queretaro",
    },
)


def enviar_pedido_evento(data):
    try:
        connection = pika.BlockingConnection(get_rabbitmq_connection_parameters())
        channel = connection.channel()
        channel.queue_declare(queue="pedidos", durable=True)
        channel.basic_publish(
            exchange="",
            routing_key="pedidos",
            body=json.dumps(data),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
    except Exception as e:
        print("Error enviando a RabbitMQ:", e)


puerto_clientes = get_service_url(
    "CLIENTES_URL",
    "CLIENTES_HOST",
    "CLIENTES_PORT",
    "http://127.0.0.1:8000",
)
puerto_productos = get_service_url(
    "PRODUCTOS_URL",
    "PRODUCTOS_HOST",
    "PRODUCTOS_PORT",
    "http://127.0.0.1:8001",
)
puerto_inventario = get_service_url(
    "INVENTARIO_URL",
    "INVENTARIO_HOST",
    "INVENTARIO_PORT",
    "http://127.0.0.1:8003",
)

FILE_NAME = get_data_file("PEDIDOS_CSV", "pedidos.csv")
HEADERS = ["id_pedido", "id_producto", "id_cliente", "cantidad", "costo"]

if not FILE_NAME.exists():
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(HEADERS)


@app.get("/health", tags=["Infra"])
def health_check():
    return {"status": "ok", "service": "pedidos"}


@app.get("/pedidos", response_model=List[Pedido])
def obtener_pedido():
    return bd_pedidos


def guardar_pedido(pedidos: List[Pedido]):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write("id_pedido,id_producto,id_cliente,cantidad,costo\n")
        for c in pedidos:
            f.write(f"{c.id_pedido},{c.id_producto},{c.id_cliente},{c.cantidad},{c.costo}\n")


def obtener_inventario_producto(id_producto: int):
    resp_inv = requests.get(f"{puerto_inventario}/inventario")
    if resp_inv.status_code != 200:
        raise HTTPException(status_code=503, detail="No se pudo consultar el inventario.")

    inventario = resp_inv.json()
    return next((i for i in inventario if i["id_producto"] == id_producto), None)


@app.post("/pedidos")
def registrar_pedido(nuevo_pedido: Pedido):
    for p in bd_pedidos:
        if p.id_pedido == nuevo_pedido.id_pedido:
            raise HTTPException(status_code=400, detail="El pedido ya existe.")

    try:
        resp_clientes = requests.get(f"{puerto_clientes}/clientes")
        if resp_clientes.status_code != 200:
            raise HTTPException(status_code=503, detail="Error en servicio de clientes")
        clientes = resp_clientes.json()

        cliente_existe = any(c["id_cliente"] == nuevo_pedido.id_cliente for c in clientes)
        if not cliente_existe:
            raise HTTPException(status_code=404, detail="El cliente no existe.")

        resp_productos = requests.get(f"{puerto_productos}/productos")
        if resp_productos.status_code != 200:
            raise HTTPException(status_code=503, detail="Error en servicio de productos")
        productos = resp_productos.json()

        producto_existe = any(p["id_producto"] == nuevo_pedido.id_producto for p in productos)
        if not producto_existe:
            raise HTTPException(status_code=404, detail="El producto no existe.")

        item_inventario = obtener_inventario_producto(nuevo_pedido.id_producto)
        if item_inventario is None:
            raise HTTPException(status_code=404, detail="El producto no tiene inventario registrado.")
        if item_inventario["cantidad"] < nuevo_pedido.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente para registrar el pedido.")

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Error de conexion con los microservicios base.")

    bd_pedidos.append(nuevo_pedido)
    guardar_pedido(bd_pedidos)

    enviar_pedido_evento(
        {
            "evento": "pedido_creado",
            "data": nuevo_pedido.dict(),
        }
    )

    return {"mensaje": "Pedido exitoso", "datos": nuevo_pedido}


@app.patch("/pedidos/{id_pedido}")
def actualizar_pedido(id_pedido: int, datos_nuevos: PedidoUpdate):
    pedido = next((p for p in bd_pedidos if p.id_pedido == id_pedido), None)

    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    if datos_nuevos.cantidad is not None and datos_nuevos.cantidad != pedido.cantidad:
        diferencia = datos_nuevos.cantidad - pedido.cantidad

        try:
            item = obtener_inventario_producto(pedido.id_producto)
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="No se pudo validar el inventario.")

        if item is None:
            raise HTTPException(status_code=404, detail="El producto no tiene inventario registrado.")

        nuevo_stock = item["cantidad"] - diferencia
        if nuevo_stock < 0:
            raise HTTPException(status_code=400, detail="Stock insuficiente para aumentar el pedido.")

        respuesta_patch = requests.patch(
            f"{puerto_inventario}/inventario/{pedido.id_producto}",
            json={"cantidad": nuevo_stock},
        )
        if respuesta_patch.status_code != 200:
            raise HTTPException(status_code=503, detail="No se pudo actualizar el inventario.")
        pedido.cantidad = datos_nuevos.cantidad

    if datos_nuevos.costo is not None:
        pedido.costo = datos_nuevos.costo

    guardar_pedido(bd_pedidos)

    return {"mensaje": "Pedido actualizado", "datos": pedido}
