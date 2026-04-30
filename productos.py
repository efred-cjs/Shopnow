from fastapi import FastAPI, HTTPException
from typing import List
import csv
import json
import os
import pika

from config import get_data_file, get_rabbitmq_connection_parameters
from datosCent import Producto, ProductoRegistro, ProductoUpdate, bd_productos

app = FastAPI(
    title="API de Productos",
    description="Este es el servicio encargado del registro basico de los productos de la empresa. \n\n"
    "Esta api actua como almacenamiento de validacion de productos. \n\n"
    "Ejecutar en puerto 8001 y los demas servicios en su respectivo puerto tal como: Pedidos (8002) y Productos (8001)",
    version="2.0.0",
    contact={
        "name": "Efren Camilo Jimenez Suarez ISC, Tecnm Queretaro",
    },
)


def enviar_evento_producto(tipo_evento, data):
    try:
        connection = pika.BlockingConnection(get_rabbitmq_connection_parameters())
        channel = connection.channel()
        channel.queue_declare(queue="productos", durable=True)

        mensaje = {
            "evento": tipo_evento,
            "data": data,
        }

        channel.basic_publish(
            exchange="",
            routing_key="productos",
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
    except Exception as e:
        print("Error enviando a RabbitMQ:", e)


FILE_NAME = get_data_file("PRODUCTOS_CSV", "productos.csv")
HEADERS = ["id_producto", "descripcion", "costo"]

if not FILE_NAME.exists():
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(HEADERS)


@app.get("/health", tags=["Infra"])
def health_check():
    return {"status": "ok", "service": "productos"}


@app.get("/productos", response_model=List[Producto])
def obtener_productos():
    return bd_productos


def guardar_productos(productos: List[Producto]):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write("id_producto,descripcion,costo\n")
        for c in productos:
            f.write(f"{c.id_producto},{c.descripcion},{c.costo}\n")


@app.post("/productos")
def registrar_producto(nuevo_producto: ProductoRegistro):
    nuevo_id = 1 if len(bd_productos) == 0 else max(p.id_producto for p in bd_productos) + 1

    producto = Producto(
        id_producto=nuevo_id,
        descripcion=nuevo_producto.descripcion,
        costo=nuevo_producto.costo,
    )
    bd_productos.append(producto)
    guardar_productos(bd_productos)

    enviar_evento_producto("producto_creado", producto.dict())
    return {"Alerta": "Producto registrado exitosamente", "id": nuevo_id}


@app.delete("/productos/{id_producto}")
def eliminar_producto(id_producto: int):
    borrar_producto = next((c for c in bd_productos if c.id_producto == id_producto), None)
    if not borrar_producto:
        raise HTTPException(status_code=404, detail=f"No se encontraron productos registrados con este ID {id_producto}")

    bd_productos.remove(borrar_producto)
    guardar_productos(bd_productos)
    enviar_evento_producto("producto_eliminado", {"id_producto": id_producto})
    return {"Alerta": f"El producto {id_producto} ha sido eliminado exitosamente de la memoria"}


@app.patch("/productos/{id_producto}")
def actualizar_producto(id_producto: int, update_datos: ProductoUpdate):
    producto_update = next((c for c in bd_productos if c.id_producto == id_producto), None)

    if not producto_update:
        raise HTTPException(status_code=404, detail=f"No se encontro el producto con ID {id_producto}")

    if update_datos.descripcion is not None:
        producto_update.descripcion = update_datos.descripcion
    if update_datos.costo is not None:
        producto_update.costo = update_datos.costo

    guardar_productos(bd_productos)
    enviar_evento_producto("producto_actualizado", producto_update.dict())
    return {"mensaje": "Producto actualizado correctamente", "datos": producto_update}
