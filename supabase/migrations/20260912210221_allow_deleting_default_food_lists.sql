DROP POLICY "Users can delete own non-default food lists"
ON public.food_lists;

CREATE POLICY "Users can delete own food lists"
ON public.food_lists
FOR DELETE
TO authenticated
USING (owner_id = auth.uid());