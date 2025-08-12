import logging
import json
import os
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions

# Leer la configuración de Cosmos DB desde las variables de entorno (local.settings.json)
try:
    ENDPOINT = os.environ['CosmosDbEndpoint']
    KEY = os.environ['CosmosDbKey']
    DATABASE_NAME = os.environ['CosmosDbDatabaseName']
    CONTAINER_NAME = os.environ['CosmosDbContainerName']
    logging.info(f"Cosmos DB config loaded: Endpoint={ENDPOINT}, Database={DATABASE_NAME}, Container={CONTAINER_NAME}")
except KeyError as e:
    logging.error(f"Error loading Cosmos DB environment variable: {e}. Ensure local.settings.json is configured correctly.")
    # Re-raise the exception or handle it to prevent the function from proceeding
    raise

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Procesando una nueva solicitud de reporte.')
    logging.info(f"Request received: {req.url}")

    # Obtener parámetros de la URL (ej: ?username=test&directorio=liquidacion-abril25)
    username = req.params.get('username')
    directorio = req.params.get('directorio')

    if not username or not directorio:
        return func.HttpResponse(
             "Por favor, provea 'username' y 'directorio' en los parámetros de la URL.",
             status_code=400
        )

    try:
        # Inicializar el cliente de Cosmos DB
        client = CosmosClient(ENDPOINT, credential=KEY)
        database = client.get_database_client(DATABASE_NAME)
        container = database.get_container_client(CONTAINER_NAME)

        # Definir la consulta SQL parametrizada para evitar inyección de SQL
        query = (
            "SELECT * FROM c WHERE c.username = @username "
            "AND c.directorio = @directorio"
        )

        # Ejecutar la consulta
        items = list(container.query_items(
            query=query,
            parameters=[
                { "name":"@username", "value": username },
                { "name":"@directorio", "value": directorio }
            ],
            enable_cross_partition_query=True
        ))

        # Calcular el monto total
        monto_total_calculado = sum(item.get('montoTotal', 0) for item in items)

        # Preparar la respuesta
        resultado = {
            'username': username,
            'directorio': directorio,
            'numero_facturas': len(items),
            'monto_total_calculado': monto_total_calculado,
            'facturas': items
        }

        return func.HttpResponse(
            json.dumps(resultado, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except exceptions.CosmosResourceNotFoundError:
        return func.HttpResponse(
            f"Error: La base de datos '{DATABASE_NAME}' o el contenedor '{CONTAINER_NAME}' no fue encontrado.",
            status_code=500
        )
    except Exception as e:
        logging.error(f"Ocurrió un error: {e}")
        return func.HttpResponse(
             "Ocurrió un error inesperado al procesar la solicitud.",
             status_code=500
        )
