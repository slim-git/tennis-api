from fastapi import Query
from typing import Dict, Literal
import httpx

def extract_type(p):
    schema = p.get("schema", {})
    if "$ref" in schema:
        return str  # fallback

    if "enum" in schema:
        return Literal[tuple(schema["enum"])]
    
    return openapi_type_to_python(schema.get("type", "string"))

def get_param_metadata(p):
    schema = p.get("schema", {})
    return {
        "name": p["name"],
        "type": extract_type(p),
        "required": p.get("required", False),
        "description": p.get("description", ""),
        "default": schema.get("default", ...),  # `...` => required if undefined
        "enum": schema.get("enum", None),
    }

async def get_remote_params(base_url: str,
                            endpoint: str,
                            method: str = 'get'):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}openapi.json")
        spec = response.json()
    
    # Extraction of the parameters from the OpenAPI spec
    path_def = spec["paths"].get(f'/{endpoint}', {})
    method_def = path_def.get(method, {})
    params = method_def.get("parameters", [])

    return [
        get_param_metadata(p)
        for p in params if p["in"] == "query"
    ]

def openapi_type_to_python(t: str):
    return {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
    }.get(t, str)  # fallback = str

def create_forward_endpoint(base_url: str, _endpoint: str, param_defs: Dict):
    # Dynamic endpoint creation
    def endpoint_factory():
        async def endpoint(**kwargs):
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}{_endpoint}",
                    params=kwargs
                )
                return response.json()
        return endpoint

    endpoint = endpoint_factory()

    # Add the parameters to the endpoint
    endpoint.__annotations__ = {
        p["name"]: openapi_type_to_python(p["type"]) for p in param_defs
    }

    # Add dependencies to the endpoint
    from inspect import Parameter, Signature

    parameters = []
    for p in param_defs:
        annotation = p["type"]
        default = p.get("default", ...) if p.get("required", False) else p.get("default", None)

        query = Query(
            default=default,
            description=p.get("description", "")
        )

        param = Parameter(
            name=p["name"],
            kind=Parameter.KEYWORD_ONLY,
            default=query,
            annotation=annotation
        )
        parameters.append(param)

    endpoint.__signature__ = Signature(parameters)

    return endpoint
