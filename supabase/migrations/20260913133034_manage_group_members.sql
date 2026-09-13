CREATE FUNCTION public.get_group_members(target_group_id bigint)
RETURNS TABLE (
    user_id uuid,
    email text,
    role text
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF NOT public.is_group_member(target_group_id) THEN
        RAISE EXCEPTION 'You are not a member of this group';
    END IF;

    RETURN QUERY
    SELECT
        group_members.user_id,
        users.email::text,
        group_members.role
    FROM public.group_members
    JOIN auth.users
        ON users.id = group_members.user_id
    WHERE group_members.group_id = target_group_id
    ORDER BY
        (group_members.role = 'owner') DESC,
        lower(users.email);
END;
$$;


CREATE FUNCTION public.add_group_member_by_email(
    target_group_id bigint,
    member_email text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    target_user_id uuid;
BEGIN
    IF NOT public.is_group_member(target_group_id) THEN
        RAISE EXCEPTION 'You are not a member of this group';
    END IF;

    IF nullif(btrim(member_email), '') IS NULL THEN
        RAISE EXCEPTION 'Email is required';
    END IF;

    SELECT id
    INTO target_user_id
    FROM auth.users
    WHERE lower(email) = lower(btrim(member_email));

    IF target_user_id IS NULL THEN
        RAISE EXCEPTION 'User not found';
    END IF;

    INSERT INTO public.group_members (
        group_id,
        user_id,
        role
    )
    VALUES (
        target_group_id,
        target_user_id,
        'member'
    )
    ON CONFLICT (group_id, user_id) DO NOTHING;
END;
$$;


REVOKE ALL
ON FUNCTION public.get_group_members(bigint)
FROM PUBLIC;

REVOKE ALL
ON FUNCTION public.add_group_member_by_email(bigint, text)
FROM PUBLIC;

GRANT EXECUTE
ON FUNCTION public.get_group_members(bigint)
TO authenticated;

GRANT EXECUTE
ON FUNCTION public.add_group_member_by_email(bigint, text)
TO authenticated;