-- Crea la tabla de auditoría para cambios de rol de usuarios
-- Ejecutar en Supabase SQL editor o psql con service_role key

CREATE TABLE IF NOT EXISTS usuario_rol_audit (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id uuid NOT NULL,
    admin_id uuid,
    old_rol text,
    new_rol text,
    changed_at timestamptz NOT NULL DEFAULT now()
);

-- Nota: `gen_random_uuid()` requiere la extensión pgcrypto. Si no está disponible,
-- reemplaza por `uuid_generate_v4()` o genera UUID desde la aplicación.
