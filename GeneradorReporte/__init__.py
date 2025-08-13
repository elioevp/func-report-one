import logging
import json
import azure.functions as func

def main(req: func.HttpRequest, documents: func.DocumentList) -> func.HttpResponse:
    logging.info('Procesando una nueva solicitud de reporte.')

    # Los documentos ya están filtrados por el binding de Cosmos DB
    # usando los parámetros 'username' y 'directorio' de la URL.

    username = req.params.get('username')
    directorio = req.params.get('directorio')

    if not documents:
        logging.warning(f"No se encontraron documentos para username='{username}' y directorio='{directorio}'.")
        # Opcional: retornar una respuesta específica si no se encuentran documentos
        return func.HttpResponse(
            json.dumps({
                'message': 'No se encontraron facturas para los criterios proporcionados.',
                'username': username,
                'directorio': directorio,
                'numero_facturas': 0,
                'monto_total_calculado': 0,
                'facturas': []
            }),
            mimetype="application/json",
            status_code=200 # O 404 si se prefiere no encontrar nada como un error
        )

    # Calcular el monto total a partir de los documentos obtenidos
    monto_total_calculado = sum(doc.get('montoTotal', 0) for doc in documents)

    # Preparar la respuesta
    resultado = {
        'username': username,
        'directorio': directorio,
        'numero_facturas': len(documents),
        'monto_total_calculado': monto_total_calculado,
        'facturas': [dict(doc) for doc in documents]  # Convertir Document a dict para serialización JSON
    }

    return func.HttpResponse(
        json.dumps(resultado, indent=2),
        mimetype="application/json",
        status_code=200
    )