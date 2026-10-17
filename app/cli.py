import argparse
import re
import secrets

from sqlalchemy import select

from app.database.db import ApiClient, SessionLocal, init_db
from app.security import hash_key

def create_client(project: str) -> None:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,50}", project):
        print("Nombre inválido: use letras, números, guion o guion bajo.")
        return
    key = "rk_" + secrets.token_urlsafe(32)
    with SessionLocal() as session:
        session.add(ApiClient(project=project, key_hash=hash_key(key)))
        session.commit()
        print(f"Cliente creado: {project}")
        print("Clave guardarla que no se volverá a mostrar:")
        print(key)

def list_clients() -> None:
    with SessionLocal() as session:
        clients = session.scalars(select(ApiClient).order_by(ApiClient.id)).all()
    if not clients:
        print("No hay clientes registrados.")
    for c in clients:
        estado = "activa" if c.status else "revocada"
        print(f"{c.id:>3}  {c.project:<20} {estado:<9} {c.created_at:%Y-%m-%d %H:%M}")

def revoke_client(client_id: int) -> None:
    with SessionLocal() as session:
        client = session.get(ApiClient, client_id)
        if client is None:
            print(f"No existe un cliente con id {client_id}.")
            return 
        client.status = False
        session.commit()
        print(f"Clave {client_id} ({client.project}) revocada.")
        

def main() -> None: 
    init_db()
    parser = argparse.ArgumentParser(description="Administrador API Keys")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-client", help="Crea una clave para un proyecto")
    create.add_argument("project")

    sub.add_parser("list", help="Lista las claves")

    revoke = sub.add_parser("revoke", help="Revoca una clave por su id")
    revoke.add_argument("client_id", type=int)

    args = parser.parse_args()
    if args.command == "create-client":
        create_client(args.project)
    elif args.command == "list":
        list_clients()
    elif args.command == "revoke":
        revoke_client(args.client_id)


if __name__ == "__main__":
    main()