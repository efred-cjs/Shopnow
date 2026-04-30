# RabbitCode en Render

Este proyecto queda listo para desplegarse en Render con los cuatro servicios (`clientes`, `productos`, `inventario`, `pedidos`) y un servicio privado de RabbitMQ.

## Que se agrego

- `render.yaml` con 5 servicios.
- `infra/rabbitmq/Dockerfile` para levantar RabbitMQ en Render.
- Variables de entorno para que los servicios descubran a RabbitMQ y a los otros microservicios.
- Persistencia por servicio usando discos montados en `/var/data`.

## Importante

Render usa filesystem efimero por defecto. Para que los CSV no se borren en cada redeploy se definieron discos persistentes.

Eso implica que en Render estos servicios deben correr en plan `starter` o superior.

## Servicios que se crean

- `rabbitcode-rabbitmq` como servicio privado
- `rabbitcode-clientes`
- `rabbitcode-productos`
- `rabbitcode-inventario`
- `rabbitcode-pedidos`

## Como desplegar

1. Sube estos cambios a tu repo en GitHub.
2. En Render crea un nuevo `Blueprint` desde tu repositorio.
3. Render detectara `render.yaml` y te mostrara los 5 servicios.
4. Confirma el despliegue.
5. Espera a que primero levante `rabbitcode-rabbitmq` y luego los servicios web.

## Persistencia de datos

Cada API guarda su CSV en su propio disco:

- `clientes` -> `/var/data/clientes.csv`
- `productos` -> `/var/data/productos.csv`
- `inventario` -> `/var/data/inventario.csv`
- `pedidos` -> `/var/data/pedidos.csv`

RabbitMQ usa su disco en:

- `/var/lib/rabbitmq`

## Endpoints de salud

Se agrego `GET /health` en:

- `clientes`
- `productos`
- `inventario`
- `pedidos`

Render los usa para verificar que cada servicio este vivo.

## Notas utiles

- Si quieres ver RabbitMQ desde fuera, cambia `rabbitcode-rabbitmq` de `type: pserv` a `type: web`.
- Si prefieres usar un RabbitMQ externo, puedes borrar ese servicio y definir `RABBITMQ_URL` manualmente en Render.
- Los servicios siguen funcionando localmente con `docker compose` y en nube con Render.
