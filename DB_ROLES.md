Roles permitidos y pasos para aplicar constraint en la BD
-----------------------------------------------------

Roles permitidos por la aplicación:

- `admin`
- `operador`
- `agronomo`
- `inversionista`

Pasos para aplicar la restricción (Postgres / Supabase):

1. Conéctate al proyecto Supabase y abre el SQL editor, o usa psql con la `service_role` key.
2. Revisa los valores actuales: `SELECT rol, COUNT(*) FROM usuario GROUP BY rol;`
3. Si hay valores inválidos, corrígelos o migrálos antes de aplicar el constraint.
4. Ejecuta el archivo `backend/db/role_constraint.sql` para añadir el CHECK constraint.

Cómo revertir:

ALTER TABLE usuario DROP CONSTRAINT IF EXISTS usuario_rol_check;

Notas:
- Aplica esto en staging primero. Si la tabla es grande, considera una migración en pasos
  (crear columna temporal, validar, swap, aplicar constraint).
