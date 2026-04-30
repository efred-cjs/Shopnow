# Dockerizacion de RabbitCode

Este proyecto queda preparado para ejecutarse como stack de contenedores con `docker compose`.

## Servicios

- `clientes` en puerto `8000`
- `productos` en puerto `8001`
- `pedidos` en puerto `8002`
- `inventario` en puerto `8003`
- `rabbitmq` en puertos `5672` y panel `15672`

## Levantar localmente

```bash
docker compose up --build
```

## Detener

```bash
docker compose down
```

## URLs

- `http://localhost:8000/docs`
- `http://localhost:8001/docs`
- `http://localhost:8002/docs`
- `http://localhost:8003/docs`
- `http://localhost:15672`

RabbitMQ por defecto:

- usuario: `guest`
- password: `guest`

## Subirlo a la nube

La forma mas simple es usar una VM o servidor con Docker instalado.

1. Copia la carpeta del proyecto al servidor.
2. Abre los puertos `8000`, `8001`, `8002`, `8003` y `15672` en el firewall si quieres acceso externo.
3. Ejecuta:

```bash
docker compose up -d --build
```

4. Tus APIs quedaran publicas en:

```text
http://TU-IP:8000/docs
http://TU-IP:8001/docs
http://TU-IP:8002/docs
http://TU-IP:8003/docs
```

## Recomendacion para produccion

Si quieres que usuarios externos entren de forma mas limpia, conviene poner un proxy reverso delante y exponer un dominio, por ejemplo:

- `api.tudominio.com/clientes`
- `api.tudominio.com/productos`
- `api.tudominio.com/pedidos`
- `api.tudominio.com/inventario`

Si quieres, el siguiente paso es dejarte tambien un `nginx` para que todo salga por un solo puerto publico.
