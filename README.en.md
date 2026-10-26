# Explain Books Like Fan Deng (think-like-fandeng)

In one sentence: turn a book or an idea into a talk the way Fan Deng does — **name the book before the reasoning, hang a story on every point, and keep turning "him" into "you."** This is a skill you install into an AI tool: you say one line, it produces content using his book-explaining method, learned from real data.

## See it work

**You say**: "Explain *The Courage to Be Disliked* the way Fan Deng would."

**You get** (excerpt):

> Why might this book offend you? Because its core idea is to take away the umbrella you're holding.
>
> What umbrella? Each of us carries a pile of "because-therefores" in our head. Because I'm not good with words, I can't manage relationships; because of my family background, I can't be happy now. Adler says: no. He proposed an idea called "separation of tasks."
>
> ... When your kid won't study, who is anxious? You are. But whose life does the consequence land on? The kid's. So that's the kid's task. You can polish the shoes and leave them by the door — a kid who wants to go to school will put them on and walk out himself.

**You say**: "Here's my book-club script — revise it the way Fan Deng would."

**It first points out**: your draft never once speaks to "you," and every point is bare concept with no story — then returns the full rewrite with at most three change notes.

More examples (12, covering all five modes) → [examples/](examples/)

## How to use

Install [SKILL.md](SKILL.md) into your AI tool (works directly with Claude Skills / ZCode skills):

| You say | You get |
|---|---|
| Explain *XXX* (a book / one chapter) like Fan Deng | A 5-minute talk script you can read aloud |
| Analyze XXX the Fan Deng way | A shareable short essay |
| Write a 2-minute script the Fan Deng way | A ready-to-read script |
| I want to chat with "Fan Deng" about XXX | A back-and-forth dialogue (first turn discloses: mimicking his thinking, not the person) |
| Here's my talk script — fix it | Top problems + full rewrite + change notes |

For tools without a skill mechanism, paste SKILL.md wholesale as the system prompt.

## Where the method comes from

Not vibes — counts. We collected Fan Deng's public book talks and interviews (60 samples, ~30 hours), transcribed everything, and coded 786 units:

- 75% of episodes open by introducing the book and author, not with a question;
- 79% of point segments are immediately followed by a story with characters and actions;
- 81–91% of segments speak directly to "you";
- When pressed with questions, 61–84% of answers give the position in the first sentence — only 3 of 96 start with a story;
- Endings favor one summary sentence; action-item lists appear in only 17%;
- Median breath (between commas): 7–9 characters.

Full method, per-finding sources, and coverage rates → [METHODOLOGY.md](METHODOLOGY.md) and [references/thinking-思维运转.md](references/thinking-思维运转.md) (Chinese).

## Repository layout

```
SKILL.md                  The skill itself: five modes + 10-step book talk + pre-delivery checklist
references/               Topic library: checks, step details, dialogue playbook, banned words (with measured frequencies), benchmark breakdowns, quote bank, all stats
METHODOLOGY.md            Full research method + evidence grading table
examples/                 12 examples covering the five modes
tools/ai_flavor_check.py  "AI-flavor" detector (baselined on 190k characters of real transcripts)
research/                 Sampling records, data tables, one-command rerunnable stats scripts
corpus/                   Corpus notes (audio and full transcripts stay out of the repo for copyright)
```

## Copyright & ethics

- Research uses only public, free content; audio and full transcripts are not published.
- Outputs are **style imitation**, never impersonation; the dialogue mode discloses in its first turn.
- Book talks summarize and explain — no long excerpts from the original books; unverifiable facts are marked "to verify."
- No use of his voice or likeness; no attacks on any author.

## License

See [LICENSE](LICENSE).
