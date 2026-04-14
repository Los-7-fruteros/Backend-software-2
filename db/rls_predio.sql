-- Políticas RLS para restringir acceso por `predio`
-- Ejecutar con la service_role key en Supabase SQL editor o psql

-- Helpers: comprobar si el usuario es admin y si tiene acceso a un predio
CREATE OR REPLACE FUNCTION public.usuario_is_admin()
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS(
        SELECT 1 FROM public.usuario u
        WHERE u.id::text = auth.uid() AND u.rol = 'admin'
    );
$$;

CREATE OR REPLACE FUNCTION public.usuario_has_access_to_predio(p_predio uuid)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS(
        SELECT 1 FROM public.usuario_predio up
        WHERE up.predio_id = p_predio
          AND up.usuario_id::text = auth.uid()
    );
$$;

-- Habilitar RLS en tablas relevantes
ALTER TABLE IF EXISTS public.predio ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.sensores ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.telemetria ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.alertas ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usuario_predio ENABLE ROW LEVEL SECURITY;

-- POLÍTICAS para `predio`
CREATE POLICY IF NOT EXISTS predio_select_for_assigned_or_admin
    ON public.predio FOR SELECT
    USING (usuario_has_access_to_predio(id) OR usuario_is_admin());

CREATE POLICY IF NOT EXISTS predio_insert_admin_only
    ON public.predio FOR INSERT
    WITH CHECK (usuario_is_admin());

CREATE POLICY IF NOT EXISTS predio_update_admin_only
    ON public.predio FOR UPDATE
    USING (usuario_is_admin())
    WITH CHECK (usuario_is_admin());

CREATE POLICY IF NOT EXISTS predio_delete_admin_only
    ON public.predio FOR DELETE
    USING (usuario_is_admin());

-- POLÍTICAS para `sensores` (tienen predio_id)
CREATE POLICY IF NOT EXISTS sensores_select_by_predio
    ON public.sensores FOR SELECT
    USING (usuario_has_access_to_predio(predio_id) OR usuario_is_admin());

CREATE POLICY IF NOT EXISTS sensores_insert_by_predio_members
    ON public.sensores FOR INSERT
    WITH CHECK (usuario_has_access_to_predio(predio_id) OR usuario_is_admin());

CREATE POLICY IF NOT EXISTS sensores_update_by_predio_members
    ON public.sensores FOR UPDATE
    USING (usuario_has_access_to_predio(predio_id) OR usuario_is_admin())
    WITH CHECK (usuario_has_access_to_predio(predio_id) OR usuario_is_admin());

CREATE POLICY IF NOT EXISTS sensores_delete_by_admin
    ON public.sensores FOR DELETE
    USING (usuario_is_admin());

-- POLÍTICAS para `telemetria` (filtrar por predio a través de sensores)
CREATE POLICY IF NOT EXISTS telemetria_select_by_sensor_predio
    ON public.telemetria FOR SELECT
    USING (
        (SELECT usuario_has_access_to_predio(s.predio_id) FROM public.sensores s WHERE s.id = telemetria.sensor_id)
        OR usuario_is_admin()
    );

CREATE POLICY IF NOT EXISTS telemetria_insert_by_sensor_predio
    ON public.telemetria FOR INSERT
    WITH CHECK (
        (SELECT usuario_has_access_to_predio(s.predio_id) FROM public.sensores s WHERE s.id = new.sensor_id)
        OR usuario_is_admin()
    );

CREATE POLICY IF NOT EXISTS telemetria_update_by_sensor_predio
    ON public.telemetria FOR UPDATE
    USING (
        (SELECT usuario_has_access_to_predio(s.predio_id) FROM public.sensores s WHERE s.id = telemetria.sensor_id)
        OR usuario_is_admin()
    )
    WITH CHECK (
        (SELECT usuario_has_access_to_predio(s.predio_id) FROM public.sensores s WHERE s.id = new.sensor_id)
        OR usuario_is_admin()
    );

CREATE POLICY IF NOT EXISTS telemetria_delete_by_admin
    ON public.telemetria FOR DELETE
    USING (usuario_is_admin());

-- POLÍTICAS para `alertas` (filtrar por predio a través de sensores)
CREATE POLICY IF NOT EXISTS alertas_select_by_sensor_predio
    ON public.alertas FOR SELECT
    USING (
        (SELECT usuario_has_access_to_predio(s.predio_id) FROM public.sensores s WHERE s.id = alertas.sensor_id)
        OR usuario_is_admin()
    );

CREATE POLICY IF NOT EXISTS alertas_insert_by_sensor_predio
    ON public.alertas FOR INSERT
    WITH CHECK (
        (SELECT usuario_has_access_to_predio(s.predio_id) FROM public.sensores s WHERE s.id = new.sensor_id)
        OR usuario_is_admin()
    );

CREATE POLICY IF NOT EXISTS alertas_update_by_sensor_predio
    ON public.alertas FOR UPDATE
    USING (
        (SELECT usuario_has_access_to_predio(s.predio_id) FROM public.sensores s WHERE s.id = alertas.sensor_id)
        OR usuario_is_admin()
    )
    WITH CHECK (
        (SELECT usuario_has_access_to_predio(s.predio_id) FROM public.sensores s WHERE s.id = new.sensor_id)
        OR usuario_is_admin()
    );

CREATE POLICY IF NOT EXISTS alertas_delete_by_admin
    ON public.alertas FOR DELETE
    USING (usuario_is_admin());

-- POLÍTICAS para usuario_predio (la propia relación)
CREATE POLICY IF NOT EXISTS usuario_predio_select_own_or_admin
    ON public.usuario_predio FOR SELECT
    USING (usuario_id::text = auth.uid() OR usuario_is_admin());

CREATE POLICY IF NOT EXISTS usuario_predio_insert_admin_only
    ON public.usuario_predio FOR INSERT
    WITH CHECK (usuario_is_admin());

CREATE POLICY IF NOT EXISTS usuario_predio_delete_admin_only
    ON public.usuario_predio FOR DELETE
    USING (usuario_is_admin());

-- NOTA: ejecutar este archivo en el SQL editor de Supabase (con service_role). Después,
-- verificar con queries de prueba que `auth.uid()` corresponde al usuario que realiza la petición
-- y que las operaciones devuelven/permiten sólo los predios asignados.
