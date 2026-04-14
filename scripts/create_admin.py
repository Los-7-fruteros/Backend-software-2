"""
Script mínimo para crear un usuario admin en Supabase y en la tabla `usuario`.

Uso (desde la carpeta `backend`):
  python scripts/create_admin.py --email admin@ejemplo.com --password Secreto123 --name "Admin"

Requiere las variables de entorno `SUPABASE_URL` y `SUPABASE_KEY` (service_role).
"""
from dotenv import load_dotenv
import os
import argparse
from supabase import create_client


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Faltan SUPABASE_URL o SUPABASE_KEY en el entorno")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # Si tenemos la service_role key, usar el admin endpoint para crear usuario
        if hasattr(supabase.auth, "admin") and hasattr(supabase.auth.admin, "create_user"):
            auth_response = supabase.auth.admin.create_user({
                "email": args.email,
                "password": args.password,
                # confirmar email por defecto cuando se crea por admin
                "email_confirm": True,
            })
        else:
            auth_response = supabase.auth.sign_up({"email": args.email, "password": args.password})
    except Exception as e:
        # Mostrar el error crudo para diagnosticar (puede venir del servicio Supabase)
        print("Error al crear usuario en Auth:", repr(e))
        return

    # Extraer user_id de varias posibles formas según la respuesta de la librería
    user_id = None
    try:
        if getattr(auth_response, "user", None):
            user_id = auth_response.user.id
        elif isinstance(auth_response, dict) and auth_response.get("user"):
            user_id = auth_response["user"].get("id")
        elif isinstance(auth_response, dict) and auth_response.get("id"):
            user_id = auth_response.get("id")
        elif hasattr(auth_response, "id"):
            user_id = auth_response.id
    except Exception:
        user_id = None

    if not user_id:
        print("No se pudo obtener el id del usuario desde la respuesta de Auth. Respuesta:", auth_response)
        return

    # Insertar en tabla usuario con rol admin
    # Algunos esquemas requieren que `hash_contrasena` no sea NULL.
    # Insertamos un valor placeholder vacío para evitar violar la constraint
    resp = supabase.table("usuario").insert({
        "id": user_id,
        "rol": "admin",
        "email": args.email,
        "hash_contrasena": "",
        "nombre": args.name,
        "num_telefono": None,
    }).execute()

    if not resp.data:
        print("Error al insertar en la tabla usuario:", resp)
        return

    print("Admin creado con id:", user_id)


if __name__ == "__main__":
    main()
