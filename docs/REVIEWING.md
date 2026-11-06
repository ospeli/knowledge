# Reviewing knowledge cards (15–30 minutes a day)

Reviewers are the people who decide what Ospeli "knows". Each approval carries your name.

1. Open the newest pull request labelled `cards`.
2. For each card:
   - Open the source link.
   - Check that the finding, setting and numbers match the source.
   - Check the evidence level: is it OE3 or really OE4?
   - Check that `lmic_applicability` is honest.
3. **Edit the card in the PR if needed.** Add `approval: {by: <your GitHub handle>, date: <today>}` and set `status: approved`. For paywalled (tier C) sources, also add `evidence.checked_by: <handle>` on each KPI.
4. **Reject** a card by deleting it from the PR, with a one-line comment saying why.
5. **Merge** when the checks pass. That night's build publishes your approved cards.

**Never approve:**
- clinical treatment advice
- anything identifying a patient or staff member
- a number you could not find in the source

## The review bot (build phase)
During the build phase, a separate Claude session, `ospeli-review-bot`, reviews each night's card pull request. It did not write the cards. It re-reads every source and checks:
- the numbers, design, evidence level, domains and setting
- that the finding is operational, not clinical

It approves cards that pass, with `approval: {by: ospeli-review-bot, kind: ai, date, notes}`. It removes cards that fail, gives a reason, and merges.

- AI-approved cards are labelled `approval_kind = ai` in the knowledge base, and answers show that label.
- Each week the founder spot-checks a random sample. Any wrong card is fixed and the error pattern goes into this guide.
- Before any hospital pilot, a human reviews the knowledge base release that will ship with it.
