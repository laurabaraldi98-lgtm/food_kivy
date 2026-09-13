CREATE OR REPLACE FUNCTION public.add_group_member_by_email(
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
    IF NOT public.is_group_owner(target_group_id) THEN
        RAISE EXCEPTION 'Only the group owner can add members';
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

    IF EXISTS (
        SELECT 1
        FROM public.group_members
        WHERE group_id = target_group_id
          AND user_id = target_user_id
    ) THEN
        RAISE EXCEPTION 'User is already a member';
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
    );
END;
$$;

REVOKE ALL
ON FUNCTION public.add_group_member_by_email(bigint, text)
FROM PUBLIC;

GRANT EXECUTE
ON FUNCTION public.add_group_member_by_email(bigint, text)
TO authenticated;