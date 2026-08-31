# Test patterns — write real tests, per stack, per AC

**Purpose.** For every dev-plan step, write tests that assert on real behaviour AND map to at least one parent AC / BR / TS. Not "here's a test template per framework" — a MAPPING RULE from acceptance items to test kinds, with pattern-matched framework style.

**Governing rule.** Tests are how `/dev:build` proves the acceptance-map at Stage 8. If a parent AC has no test row, the map is incomplete and Stage 8 fails.

---

## 1. What kind of test for what kind of assertion

Given a parent-owned assertion (AC / BR / TS / NFR), pick the test kind:

| Assertion shape | Test kind | Where |
|---|---|---|
| Endpoint returns X on valid input | Integration / contract test | Backend sub-task |
| Endpoint returns X on error input | Integration test | Backend sub-task |
| Business rule enforced on write | Unit test on the service + integration on the endpoint | Backend sub-task |
| DB constraint (e.g. uniqueness) | Migration test OR integration test hitting the constraint | Backend / DB sub-task |
| UI form submission wired to endpoint | Component test (form validation) + integration test (form → mocked API) | Frontend sub-task |
| UI error display on server refusal | Component test with mocked error response | Frontend sub-task |
| Full user flow (submit → toast → list update) | E2E test | Last sub-task to land closes; otherwise deferred |
| Performance NFR (< 300ms p95) | Benchmark / load test | Backend sub-task |
| Security NFR (rate-limiting, authz) | Integration test | Backend sub-task |

---

## 2. Unit test template — behavioural, not tautological

**A test is behavioural when:** it exercises real code paths and asserts on real outputs / state changes. It's tautological when it mocks the SUT and asserts that the mock returned what it was told to return.

### Anti-patterns to reject

```typescript
// ❌ Tautological — proves nothing
it('creates a supplier', () => {
  const service = mock(SupplierService);
  service.create.mockResolvedValue({ id: '1', name: 'X' });
  expect(await service.create({ name: 'X' })).toEqual({ id: '1', name: 'X' });
});

// ❌ Only-happy-path — misses BR / edge-case coverage
it('creates a supplier', async () => {
  const result = await service.create({ name: 'X', taxId: '123', country: 'US' });
  expect(result.id).toBeDefined();
});
```

### Good pattern — real state, real assertion, real error paths

```typescript
// ✅ Real service, real repo (in-memory or test DB), real assertions
describe('SupplierService.create', () => {
  let service: SupplierService;
  let repo: SupplierRepository;

  beforeEach(async () => {
    repo = new InMemorySupplierRepository();      // real class, real state
    service = new SupplierService(repo, /* deps */);
  });

  it('creates a draft supplier with generated id (happy path — AC-B1)', async () => {
    const result = await service.create({ taxId: '123', country: 'US', name: 'Acme' });
    expect(result.id).toMatch(/^SUP-/);
    expect(await repo.findById(result.id)).toEqual(
      expect.objectContaining({ status: 'draft', taxId: '123', country: 'US' }),
    );
  });

  it('refuses duplicate (tax_id, country) — AC-B2 · BR-1', async () => {
    await service.create({ taxId: '123', country: 'US', name: 'Acme' });
    await expect(
      service.create({ taxId: '123', country: 'US', name: 'Duplicate' }),
    ).rejects.toThrow(DuplicateSupplierError);
  });

  it('accepts same tax_id in different countries — BR-1 edge case', async () => {
    await service.create({ taxId: '123', country: 'US', name: 'Acme US' });
    const second = await service.create({ taxId: '123', country: 'DE', name: 'Acme DE' });
    expect(second.id).toBeDefined();
  });

  it('leaves no partial state when compliance service fails — AC-B3', async () => {
    const failing = new FailingComplianceService();
    service = new SupplierService(repo, failing);
    await expect(
      service.create({ taxId: '999', country: 'US', name: 'Fail' }),
    ).rejects.toThrow(ComplianceServiceError);
    expect(await repo.findAll()).toHaveLength(0);
  });
});
```

Note the comment tags — every test cites the parent AC / BR it maps to. **Every test file writes these tags** so `/dev:build` Stage 8 can build the acceptance-map programmatically.

---

## 3. Integration / API contract test template

For an endpoint the sub-task creates or modifies:

```typescript
describe('POST /supplier (AC-B1, AC-B2, AC-B3, BR-1)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const testModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(ComplianceService)
      .useClass(TestComplianceService)   // real class, testable configuration
      .compile();
    app = testModule.createNestApplication();
    await app.init();
  });

  afterAll(async () => await app.close());

  it('201 with created record on valid input — AC-B1', async () => {
    const res = await request(app.getHttpServer())
      .post('/supplier')
      .send({ taxId: '111', country: 'US', name: 'Acme' })
      .expect(201);
    expect(res.body).toMatchObject({
      id:      expect.stringMatching(/^SUP-/),
      taxId:   '111',
      country: 'US',
      status:  'draft',
    });
  });

  it('409 with DUPLICATE_TAX_ID on repeat — AC-B2', async () => {
    await request(app.getHttpServer())
      .post('/supplier')
      .send({ taxId: '222', country: 'US', name: 'Once' })
      .expect(201);
    const res = await request(app.getHttpServer())
      .post('/supplier')
      .send({ taxId: '222', country: 'US', name: 'Twice' })
      .expect(409);
    expect(res.body).toEqual({ code: 'DUPLICATE_TAX_ID' });
  });

  it('503 with COMPLIANCE_UNAVAILABLE when service is down — AC-B3', async () => {
    // Force the TestComplianceService into failure mode via its DI hook
    (app.get(ComplianceService) as TestComplianceService).setMode('failure');
    const res = await request(app.getHttpServer())
      .post('/supplier')
      .send({ taxId: '333', country: 'US', name: 'Down' })
      .expect(503);
    expect(res.body).toEqual({ code: 'COMPLIANCE_UNAVAILABLE' });
  });

  it('400 on missing tax_id (validation)', async () => {
    const res = await request(app.getHttpServer())
      .post('/supplier')
      .send({ country: 'US', name: 'NoTaxId' })
      .expect(400);
    expect(res.body.errors).toContain(expect.stringMatching(/tax_id/i));
  });
});
```

**Every distinct message** in the `Refusals` table from `tl-plan.md` / `implementation.md` §2 gets ONE test. Three 409s → three tests.

---

## 4. E2E test template

Only run E2E when this task is the LAST sub-task to land (per parent's rollup Sub-tasks table). Otherwise mark deferred-to-e2e in the acceptance-map.

```typescript
test('Supplier onboarding — end-to-end (AC-1, AC-2)', async ({ page }) => {
  // AC-1: submit valid form → success toast → record appears in list
  await page.goto('/suppliers/new');
  await page.getByLabel('Tax ID').fill('999');
  await page.getByLabel('Country').selectOption('US');
  await page.getByLabel('Name').fill('E2E Supplier');
  await page.getByRole('button', { name: 'Submit' }).click();

  await expect(page.getByRole('status')).toContainText(/created/i);
  await expect(page).toHaveURL(/\/suppliers$/);
  await expect(page.getByRole('row', { name: /E2E Supplier/i })).toBeVisible();

  // AC-2: duplicate → inline error, no toast
  await page.getByRole('link', { name: 'New Supplier' }).click();
  await page.getByLabel('Tax ID').fill('999');
  await page.getByLabel('Country').selectOption('US');
  await page.getByLabel('Name').fill('Attempted Duplicate');
  await page.getByRole('button', { name: 'Submit' }).click();

  await expect(page.getByText(/already registered/i)).toBeVisible();
  await expect(page.getByRole('status')).not.toBeVisible();
});
```

---

## 5. Framework-specific idioms — inferred from Phase 2, applied here

Because `pattern-inference.md` already read a test file and recorded the mocking + assertion style, this file's templates are agnostic. When actually writing:

- Use the mocking approach from `inferred_patterns.testing.mocking`
- Use the assertion style from `inferred_patterns.testing.assertions`
- Put files at the location from `inferred_patterns.testing.location`
- Use fixture location from `inferred_patterns.testing.fixtures`

If the repo uses `vi.mock(...)` (Vitest) instead of `jest.mock(...)` — the template above swaps to `vi.mock`. Same shape, different name.

---

## 6. Test-to-AC mapping — the machine-readable link

Every test's docstring / describe / it block MUST cite the parent AC / BR / TS ids it covers. Format:

```typescript
it('should <behaviour> — AC-B1, AC-B2 · BR-1', ...)
```

Or in Python:

```python
def test_creates_supplier():
    """AC-B1, AC-B2 · BR-1: <behaviour>"""
    ...
```

`/dev:build` Stage 8 greps for these ID references to fill the `Verified by` column in `acceptance-map.md`. Missing tag → test doesn't count toward acceptance-map completion.

---

## 7. Test data — no secrets, no real IDs

- Tax IDs, emails, phone numbers: synthetic (`123`, `test@example.com`, `+15555550100`)
- API keys, tokens: `TEST_KEY_<uuid>` — never real credentials
- File fixtures: small, checked-in binaries or synthetic generation

---

## 8. Retry / flake avoidance

- No `sleep(N)` — use test framework's `waitFor` / `eventually`
- No random data unless seeded (`Math.random()` in tests without a seed is a bug)
- No dependency on wall-clock ordering — use dependency-injected clocks or freeze time (`vi.useFakeTimers`, `freezegun`, etc.)

Flaky tests = failed tests. If a test can't be made stable, escalate rather than skip.

---

## 9. When you can't write a test

Rare: a step is genuinely infrastructure (config wiring, DI module registration) with no behavioural surface to test. In that case, no test is fine — but note in `implementation-log.md`:

```yaml
step_<n>:
  test_written:  false
  reason:        infra-only step (DI registration in supplier.module.ts); no behavioural assertion applicable
```

`/dev:build` Stage 8 will accept these as `covered-by-infra` rows in the acceptance-map.

**Don't abuse this** — if 3 out of 10 steps have no test, something is wrong with the plan.
