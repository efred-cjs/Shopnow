# RabbitCode en Render Free

Esta version del proyecto queda preparada para subirse a Render usando solo `Web Services` gratuitos.

## Como funciona esta version

- `clientes`, `productos`, `inventario` y `pedidos` se despliegan como 4 servicios separados.
- RabbitMQ queda desactivado en Render con `ENABLE_RABBITMQ=false`.
- Los pedidos se validan por HTTP y descuentan inventario por HTTP.
- Los CSV siguen funcionando, pero en Render Free no son persistentes.

## Importante

En Render Free el filesystem es temporal. Eso significa que si un servicio se reinicia, se redeploya o se duerme por inactividad, sus archivos CSV pueden perderse.

Esta configuracion sirve para demo, pruebas y exposicion del proyecto. No sirve como almacenamiento permanente.

## Configuracion de cada Web Service

Usa el mismo repositorio y la misma rama para los 4 servicios.

### 1. Servicio `clientes`

- Name: `rabbitcode-clientes`
- Runtime: `Python 3`
- Plan: `Free`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn clientes:app --host 0.0.0.0 --port $PORT`

Environment Variables:

- `ENABLE_RABBITMQ=false`
- `CLIENTES_CSV=clientes.csv`

### 2. Servicio `productos`

- Name: `rabbitcode-productos`
- Runtime: `Python 3`
- Plan: `Free`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn productos:app --host 0.0.0.0 --port $PORT`

Environment Variables:

- `ENABLE_RABBITMQ=false`
- `PRODUCTOS_CSV=productos.csv`

### 3. Servicio `inventario`

- Name: `rabbitcode-inventario`
- Runtime: `Python 3`
- Plan: `Free`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn inventario:app --host 0.0.0.0 --port $PORT`

Environment Variables:

- `ENABLE_RABBITMQ=false`
- `INVENTARIO_CSV=inventario.csv`
- `PRODUCTOS_URL=https://AQUI-LA-URL-DE-PRODUCTOS.onrender.com`

### 4. Servicio `pedidos`

- Name: `rabbitcode-pedidos`
- Runtime: `Python 3`
- Plan: `Free`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn pedidos:app --host 0.0.0.0 --port $PORT`

Environment Variables:

- `ENABLE_RABBITMQ=false`
- `PEDIDOS_CSV=pedidos.csv`
- `CLIENTES_URL=https://AQUI-LA-URL-DE-CLIENTES.onrender.com`
- `PRODUCTOS_URL=https://AQUI-LA-URL-DE-PRODUCTOS.onrender.com`
- `INVENTARIO_URL=https://AQUI-LA-URL-DE-INVENTARIO.onrender.com`

## Orden recomendado de despliegue

1. Despliega `clientes`.
2. Despliega `productos`.
3. Despliega `inventario`.
4. Copia la URL publica de `productos` y pegala en `PRODUCTOS_URL` de `inventario`.
5. Despliega `pedidos`.
6. Copia las URLs publicas de `clientes`, `productos` e `inventario` y pegalas en las variables de `pedidos`.
7. Haz un manual deploy de `inventario` y `pedidos` despues de guardar variables.

## Endpoints de verificacion

- `https://tu-servicio-clientes.onrender.com/health`
- `https://tu-servicio-productos.onrender.com/health`
- `https://tu-servicio-inventario.onrender.com/health`
- `https://tu-servicio-pedidos.onrender.com/health`

## Flujo de prueba recomendado

1. Crear un cliente en `/clientes`.
2. Crear un producto en `/productos`.
3. Registrar inventario en `/inventario`.
4. Crear un pedido en `/pedidos`.
5. Consultar `/inventario` y verificar que el stock bajo.

## Que ya no necesitas para Render Free

- `render.yaml`
- RabbitMQ en Render
- discos persistentes

## Recomendacion futura

Si despues quieres que los datos no se pierdan, el siguiente paso correcto es mover `clientes`, `productos`, `inventario` y `pedidos` de CSV a una base de datos como Render Postgres.
