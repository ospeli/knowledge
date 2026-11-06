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
