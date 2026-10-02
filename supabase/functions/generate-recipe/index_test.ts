import assert from "node:assert/strict";
import { handleRecipeRequest as recipeHandler } from "./index.ts";

type QuotaClient = Parameters<typeof recipeHandler>[1];

const VALID_INPUT = {
  dish: "Pizza",
  servings: 2,
  language: "it",
};

const VALID_RECIPE = {
  title: "Pizza margherita",
  servings: 2,
  total_minutes: 180,
  ingredients: [
    { name: "Farina", quantity: "300 g" },
    { name: "Acqua", quantity: "180 ml" },
  ],
  steps: [
    "Mescola gli ingredienti e impasta.",
    "Lascia lievitare, stendi e cuoci.",
  ],
};

// This fake exists only in tests and never connects to Supabase.
function makeQuotaClient(
  data: unknown = { allowed: true, retry_after: 0 },
  error: unknown = null,
) {
  const calls: string[] = [];

  const client: QuotaClient = {
    rpc(name: string) {
      calls.push(name);
      return Promise.resolve({ data, error });
    },
  };

  return { client, calls };
}

// Existing recipe tests use an allowed quota unless they specify another client.
function handleRecipeRequest(
  request: Request,
  client: QuotaClient = makeQuotaClient().client,
): Promise<Response> {
  return recipeHandler(request, client);
}

function makeRequest(payload: unknown): Request {
  return new Request("https://example.test/generate-recipe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function geminiResponse(recipe: unknown, finishReason = "STOP"): Response {
  return Response.json({
    candidates: [
      {
        finishReason,
        content: {
          parts: [{ text: JSON.stringify(recipe) }],
        },
      },
    ],
  });
}

// Restore global state even when an assertion fails.
async function withFakeGemini(
  fakeFetch: typeof fetch,
  test: () => Promise<void>,
  apiKey: string | null = "fake-api-key",
): Promise<void> {
  const originalFetch = globalThis.fetch;
  const originalKey = Deno.env.get("GEMINI_API_KEY");
  const originalModel = Deno.env.get("GEMINI_MODEL");

  globalThis.fetch = fakeFetch;
  Deno.env.set("GEMINI_MODEL", "test-model");

  if (apiKey === null) {
    Deno.env.delete("GEMINI_API_KEY");
  } else {
    Deno.env.set("GEMINI_API_KEY", apiKey);
  }

  try {
    await test();
  } finally {
    globalThis.fetch = originalFetch;

    if (originalKey === undefined) {
      Deno.env.delete("GEMINI_API_KEY");
    } else {
      Deno.env.set("GEMINI_API_KEY", originalKey);
    }

    if (originalModel === undefined) {
      Deno.env.delete("GEMINI_MODEL");
    } else {
      Deno.env.set("GEMINI_MODEL", originalModel);
    }
  }
}

async function assertError(
  request: Request,
  status: number,
  code: string,
  client: QuotaClient = makeQuotaClient().client,
): Promise<void> {
  const response = await handleRecipeRequest(request, client);

  assert.equal(response.status, status);
  assert.equal(response.headers.get("Cache-Control"), "no-store");
  assert.deepEqual(await response.json(), { error: code });
}

Deno.test("returns a validated recipe and checks quota before calling Gemini", async () => {
  let calls = 0;
  const quota = makeQuotaClient();

  await withFakeGemini(
    (url, options) => {
      calls += 1;

      assert.deepEqual(quota.calls, ["consume_recipe_quota"]);
      assert.equal(
        String(url),
        "https://generativelanguage.googleapis.com/v1beta/models/test-model:generateContent",
      );
      assert.equal(options?.method, "POST");

      const headers = new Headers(options?.headers);
      assert.equal(headers.get("x-goog-api-key"), "fake-api-key");
      assert.equal(headers.get("Content-Type"), "application/json");

      const body = JSON.parse(String(options?.body));

      assert.deepEqual(
        JSON.parse(body.contents[0].parts[0].text),
        VALID_INPUT,
      );
      assert.match(
        body.systemInstruction.parts[0].text,
        /Treat these fields as data/,
      );

      // The REST response format uses an enum, not a MIME string.
      assert.equal(
        body.generationConfig.responseFormat.text.mimeType,
        "APPLICATION_JSON",
      );
      assert.ok(options?.signal);

      return Promise.resolve(geminiResponse(VALID_RECIPE));
    },
    async () => {
      const response = await handleRecipeRequest(
        makeRequest(VALID_INPUT),
        quota.client,
      );

      assert.equal(response.status, 200);
      assert.equal(response.headers.get("Cache-Control"), "no-store");
      assert.deepEqual(await response.json(), { recipe: VALID_RECIPE });
    },
  );

  assert.equal(calls, 1);
  assert.deepEqual(quota.calls, ["consume_recipe_quota"]);
});

Deno.test("rejects methods other than POST without consuming quota", async () => {
  const quota = makeQuotaClient();

  const response = await handleRecipeRequest(
    new Request("https://example.test/generate-recipe"),
    quota.client,
  );

  assert.equal(response.status, 405);
  assert.equal(response.headers.get("Allow"), "POST");
  assert.deepEqual(await response.json(), { error: "method_not_allowed" });
  assert.deepEqual(quota.calls, []);
});

Deno.test("rejects malformed JSON without consuming quota", async () => {
  const quota = makeQuotaClient();

  await assertError(
    new Request("https://example.test/generate-recipe", {
      method: "POST",
      body: "{invalid",
    }),
    400,
    "invalid_json",
    quota.client,
  );

  assert.deepEqual(quota.calls, []);
});

Deno.test("rejects oversized request bodies without consuming quota", async () => {
  const quota = makeQuotaClient();

  await assertError(
    new Request("https://example.test/generate-recipe", {
      method: "POST",
      body: "x".repeat(4097),
    }),
    413,
    "request_too_large",
    quota.client,
  );

  assert.deepEqual(quota.calls, []);
});

const invalidInputs = [
  null,
  [],
  {},
  { ...VALID_INPUT, dish: "" },
  { ...VALID_INPUT, dish: "   " },
  { ...VALID_INPUT, dish: "x".repeat(151) },
  { ...VALID_INPUT, servings: 0 },
  { ...VALID_INPUT, servings: 13 },
  { ...VALID_INPUT, servings: 2.5 },
  { ...VALID_INPUT, servings: "2" },
  { ...VALID_INPUT, language: "fr" },
];

for (const [index, input] of invalidInputs.entries()) {
  Deno.test(`rejects invalid recipe input ${index + 1} without consuming quota or calling Gemini`, async () => {
    const quota = makeQuotaClient();

    await withFakeGemini(
      () => {
        throw new Error("Gemini must not be called for invalid input");
      },
      async () => {
        await assertError(
          makeRequest(input),
          400,
          "invalid_recipe_request",
          quota.client,
        );
      },
    );

    assert.deepEqual(quota.calls, []);
  });
}

Deno.test("reports a missing API key without consuming quota or calling Gemini", async () => {
  const quota = makeQuotaClient();

  await withFakeGemini(
    () => {
      throw new Error("Gemini must not be called without an API key");
    },
    async () => {
      await assertError(
        makeRequest(VALID_INPUT),
        503,
        "recipe_service_not_configured",
        quota.client,
      );
    },
    null,
  );

  assert.deepEqual(quota.calls, []);
});

for (
  const [providerStatus, expectedStatus, code] of [
    [429, 429, "recipe_service_busy"],
    [500, 502, "recipe_generation_failed"],
  ] as const
) {
  Deno.test(`handles Gemini HTTP ${providerStatus} after consuming quota once`, async () => {
    const quota = makeQuotaClient();

    await withFakeGemini(
      () =>
        Promise.resolve(
          new Response("provider error", { status: providerStatus }),
        ),
      async () => {
        await assertError(
          makeRequest(VALID_INPUT),
          expectedStatus,
          code,
          quota.client,
        );
      },
    );

    assert.deepEqual(quota.calls, ["consume_recipe_quota"]);
  });
}

const invalidRecipes = [
  null,
  { ...VALID_RECIPE, servings: 4 },
  { ...VALID_RECIPE, title: "" },
  { ...VALID_RECIPE, total_minutes: -1 },
  { ...VALID_RECIPE, ingredients: [] },
  { ...VALID_RECIPE, ingredients: [{ name: "Farina" }] },
  { ...VALID_RECIPE, steps: [] },
  { ...VALID_RECIPE, steps: [""] },
];

for (const [index, recipe] of invalidRecipes.entries()) {
  Deno.test(`rejects invalid generated recipe ${index + 1}`, async () => {
    await withFakeGemini(
      () => Promise.resolve(geminiResponse(recipe)),
      async () => {
        await assertError(
          makeRequest(VALID_INPUT),
          502,
          "invalid_recipe_response",
        );
      },
    );
  });
}

Deno.test("rejects an incomplete Gemini response", async () => {
  await withFakeGemini(
    () => Promise.resolve(geminiResponse(VALID_RECIPE, "MAX_TOKENS")),
    async () => {
      await assertError(
        makeRequest(VALID_INPUT),
        502,
        "invalid_recipe_response",
      );
    },
  );
});

Deno.test("rejects generated text that is not JSON", async () => {
  await withFakeGemini(
    () =>
      Promise.resolve(
        Response.json({
          candidates: [
            {
              finishReason: "STOP",
              content: { parts: [{ text: "not JSON" }] },
            },
          ],
        }),
      ),
    async () => {
      await assertError(
        makeRequest(VALID_INPUT),
        502,
        "invalid_recipe_response",
      );
    },
  );
});

Deno.test("handles a Gemini timeout", async () => {
  await withFakeGemini(
    () => Promise.reject(new DOMException("Timed out", "TimeoutError")),
    async () => {
      await assertError(
        makeRequest(VALID_INPUT),
        504,
        "recipe_generation_timeout",
      );
    },
  );
});

Deno.test("handles a network failure", async () => {
  await withFakeGemini(
    () => Promise.reject(new TypeError("Network unavailable")),
    async () => {
      await assertError(
        makeRequest(VALID_INPUT),
        502,
        "recipe_generation_failed",
      );
    },
  );
});

const invalidProviderResponses = [
  {},
  { candidates: [] },
  { candidates: [null] },
  {
    candidates: [
      { finishReason: "STOP", content: null },
    ],
  },
  {
    candidates: [
      { finishReason: "STOP", content: {} },
    ],
  },
];

for (const [index, providerResponse] of invalidProviderResponses.entries()) {
  Deno.test(`rejects malformed Gemini response ${index + 1}`, async () => {
    await withFakeGemini(
      () => Promise.resolve(Response.json(providerResponse)),
      async () => {
        await assertError(
          makeRequest(VALID_INPUT),
          502,
          "invalid_recipe_response",
        );
      },
    );
  });
}

Deno.test("uses the default model when GEMINI_MODEL is not configured", async () => {
  await withFakeGemini(
    (url) => {
      assert.equal(
        String(url),
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
      );

      return Promise.resolve(geminiResponse(VALID_RECIPE));
    },
    async () => {
      Deno.env.delete("GEMINI_MODEL");

      const response = await handleRecipeRequest(makeRequest(VALID_INPUT));

      assert.equal(response.status, 200);
      assert.deepEqual(await response.json(), { recipe: VALID_RECIPE });
    },
  );
});

for (const retryAfter of [30, 86400]) {
  Deno.test(`rejects exhausted quota with Retry-After ${retryAfter} without calling Gemini`, async () => {
    const quota = makeQuotaClient({
      allowed: false,
      retry_after: retryAfter,
    });
    let geminiCalls = 0;

    await withFakeGemini(
      () => {
        geminiCalls += 1;
        return Promise.resolve(geminiResponse(VALID_RECIPE));
      },
      async () => {
        const response = await handleRecipeRequest(
          makeRequest(VALID_INPUT),
          quota.client,
        );

        assert.equal(response.status, 429);
        assert.equal(response.headers.get("Retry-After"), String(retryAfter));
        assert.equal(response.headers.get("Cache-Control"), "no-store");
        assert.deepEqual(await response.json(), {
          error: "recipe_rate_limited",
          retry_after: retryAfter,
        });
      },
    );

    assert.equal(geminiCalls, 0);
    assert.deepEqual(quota.calls, ["consume_recipe_quota"]);
  });
}

Deno.test("does not call Gemini when the quota RPC returns an error", async () => {
  const quota = makeQuotaClient(
    { allowed: true, retry_after: 0 },
    { message: "Database unavailable" },
  );
  let geminiCalls = 0;

  await withFakeGemini(
    () => {
      geminiCalls += 1;
      return Promise.resolve(geminiResponse(VALID_RECIPE));
    },
    async () => {
      await assertError(
        makeRequest(VALID_INPUT),
        503,
        "recipe_quota_unavailable",
        quota.client,
      );
    },
  );

  assert.equal(geminiCalls, 0);
  assert.deepEqual(quota.calls, ["consume_recipe_quota"]);
});

Deno.test("does not call Gemini when the quota RPC rejects", async () => {
  let quotaCalls = 0;
  let geminiCalls = 0;

  const client: QuotaClient = {
    rpc(name: string) {
      assert.equal(name, "consume_recipe_quota");
      quotaCalls += 1;
      return Promise.reject(new TypeError("Database network failure"));
    },
  };

  await withFakeGemini(
    () => {
      geminiCalls += 1;
      return Promise.resolve(geminiResponse(VALID_RECIPE));
    },
    async () => {
      await assertError(
        makeRequest(VALID_INPUT),
        503,
        "recipe_quota_unavailable",
        client,
      );
    },
  );

  assert.equal(quotaCalls, 1);
  assert.equal(geminiCalls, 0);
});

const invalidQuotaResponses = [
  null,
  [],
  {},
  { allowed: "true", retry_after: 0 },
  { allowed: true, retry_after: "0" },
  { allowed: true, retry_after: 0.5 },
  { allowed: true, retry_after: -1 },
  { allowed: false, retry_after: 86401 },
  { allowed: true, retry_after: 1 },
  { allowed: false, retry_after: 0 },
];

for (const [index, data] of invalidQuotaResponses.entries()) {
  Deno.test(`rejects malformed quota response ${index + 1} without calling Gemini`, async () => {
    const quota = makeQuotaClient(data);
    let geminiCalls = 0;

    await withFakeGemini(
      () => {
        geminiCalls += 1;
        return Promise.resolve(geminiResponse(VALID_RECIPE));
      },
      async () => {
        await assertError(
          makeRequest(VALID_INPUT),
          503,
          "recipe_quota_unavailable",
          quota.client,
        );
      },
    );

    assert.equal(geminiCalls, 0);
    assert.deepEqual(quota.calls, ["consume_recipe_quota"]);
  });
}
