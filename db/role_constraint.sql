-- SQL para añadir un CHECK constraint que valida los roles permitidos
-- Ejecutar en la base de datos (psql o Supabase SQL editor)

ALTER TABLE usuario
ADD CONSTRAINT usuario_rol_check
CHECK (rol IN ('admin','operador','agronomo','inversionista'));

-- Nota: si la tabla ya contiene valores fuera de esta lista, el comando fallará.
-- Revise los datos actuales antes de aplicar en producción.
