ALTER TABLE public.food_lists
    ALTER COLUMN owner_id DROP NOT NULL;

ALTER TABLE public.food_lists
    ADD COLUMN group_id bigint
    REFERENCES public.groups(id)
    ON DELETE CASCADE;

ALTER TABLE public.food_lists
    ADD CONSTRAINT food_lists_owner_or_group
    CHECK (
        (
            owner_id IS NOT NULL
            AND group_id IS NULL
        )
        OR
        (
            owner_id IS NULL
            AND group_id IS NOT NULL
        )
    );

ALTER TABLE public.food_lists
    ADD CONSTRAINT group_lists_cannot_be_default
    CHECK (
        group_id IS NULL
        OR is_default = false
    );


CREATE FUNCTION public.can_access_food_list(
    target_list_id bigint
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.food_lists
        WHERE id = target_list_id
          AND (
              owner_id = auth.uid()
              OR (
                  group_id IS NOT NULL
                  AND public.is_group_member(group_id)
              )
          )
    );
$$;

REVOKE ALL
ON FUNCTION public.can_access_food_list(bigint)
FROM PUBLIC;

GRANT EXECUTE
ON FUNCTION public.can_access_food_list(bigint)
TO authenticated;


DROP POLICY IF EXISTS "Users can read own food lists"
ON public.food_lists;

DROP POLICY IF EXISTS "Users can create own food lists"
ON public.food_lists;

DROP POLICY IF EXISTS "Users can rename own food lists"
ON public.food_lists;

DROP POLICY IF EXISTS "Users can delete own food lists"
ON public.food_lists;

DROP POLICY IF EXISTS "Users can delete own non-default food lists"
ON public.food_lists;


CREATE POLICY "Users can read accessible food lists"
ON public.food_lists
FOR SELECT
TO authenticated
USING (
    owner_id = auth.uid()
    OR (
        group_id IS NOT NULL
        AND public.is_group_member(group_id)
    )
);


CREATE POLICY "Users can create accessible food lists"
ON public.food_lists
FOR INSERT
TO authenticated
WITH CHECK (
    (
        owner_id = auth.uid()
        AND group_id IS NULL
        AND is_default = false
    )
    OR
    (
        owner_id IS NULL
        AND group_id IS NOT NULL
        AND is_default = false
        AND public.is_group_member(group_id)
    )
);


CREATE POLICY "Users can rename accessible food lists"
ON public.food_lists
FOR UPDATE
TO authenticated
USING (
    owner_id = auth.uid()
    OR (
        group_id IS NOT NULL
        AND public.is_group_member(group_id)
    )
)
WITH CHECK (
    owner_id = auth.uid()
    OR (
        group_id IS NOT NULL
        AND public.is_group_member(group_id)
    )
);


CREATE POLICY "Owners can delete accessible food lists"
ON public.food_lists
FOR DELETE
TO authenticated
USING (
    (
        owner_id = auth.uid()
        AND group_id IS NULL
    )
    OR
    (
        group_id IS NOT NULL
        AND public.is_group_owner(group_id)
    )
);


DROP POLICY IF EXISTS "Users can read foods in own lists"
ON public.foods;

DROP POLICY IF EXISTS "Users can add foods to own lists"
ON public.foods;

DROP POLICY IF EXISTS "Users can update foods in own lists"
ON public.foods;

DROP POLICY IF EXISTS "Users can delete foods in own lists"
ON public.foods;


CREATE POLICY "Users can read foods in accessible lists"
ON public.foods
FOR SELECT
TO authenticated
USING (
    public.can_access_food_list(list_id)
);


CREATE POLICY "Users can add foods to accessible lists"
ON public.foods
FOR INSERT
TO authenticated
WITH CHECK (
    public.can_access_food_list(list_id)
);


CREATE POLICY "Users can update foods in accessible lists"
ON public.foods
FOR UPDATE
TO authenticated
USING (
    public.can_access_food_list(list_id)
)
WITH CHECK (
    public.can_access_food_list(list_id)
);


CREATE POLICY "Users can delete foods in accessible lists"
ON public.foods
FOR DELETE
TO authenticated
USING (
    public.can_access_food_list(list_id)
);