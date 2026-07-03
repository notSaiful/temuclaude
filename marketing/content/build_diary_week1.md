# BUILD DIARY — WEEK 1

## Tweet (Monday)
Day 1 of building Timuclaude in public.

Today: restructured the fusion module. 3 models now answer simultaneously instead of sequentially. 40% faster.

Still slower than a single model. But the accuracy improvement is worth it.

Speed vs correctness. I'll take correctness.

## Tweet (Tuesday)
Day 2: Fixed a caching bug.

Turns out I was sending duplicate API requests when models gave similar answers. One cache lookup fixed it.

Token costs dropped 35% with one line of code.

Sometimes the best optimization is just not asking the same question twice.

## Tweet (Wednesday)
Day 3: Tried MCTS for reasoning enhancement.

Result: 2x slower, only 3% more accurate. Not worth it. Yet.

What I learned: the tree needs better pruning. Rollouts need diversity, not repetition.

Tomorrow: diversity-based pruning with temperature variation.

This is what building AI orchestration actually looks like. Not a straight line.

## Tweet (Thursday)
Day 4: The research scout found 3 new papers on process reward models.

The idea: instead of judging the final answer, judge each STEP that led to it.

If we can verify the reasoning process, not just the output, accuracy could jump significantly.

Reading through them now. More soon.

## Tweet (Friday)
Day 5: Week 1 recap.

- Fusion restructured (40% faster)
- Caching fixed (35% cost reduction)
- MCTS tried and shelved (not ready yet)
- 3 new research papers discovered

Next week: self-QA improvements and first formal benchmark vs GPT-5.6 Sol.

Building in public means showing the dead ends too. There are a lot of dead ends.

## Tweet (Saturday)
Day 6: Deep-dive into the fusion algorithm.

Current approach: weighted voting based on confidence scores.

Problem: models that are confidently wrong get too much weight.

New idea: penalize confidence when models disagree. If 2 say A and 1 says B, the one saying B should lose confidence, not just votes.

Testing this tomorrow.

## Tweet (Sunday)
Day 7: Planning day.

Next week's goals:
- Implement confidence penalty for disagreement
- Run first formal benchmark vs GPT-5.6 Sol
- Write the origin story thread
- Set up scheduled posting

Public commitment: beat GPT-5.6 Sol on at least one benchmark by end of next week.

I'll post results either way.