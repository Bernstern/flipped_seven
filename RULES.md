# Flip 7 Tournament Rules

## Objective
First to 200 points across multiple rounds. Draw cards to collect up to 7 unique numbers without busting.

## Deck (94 cards)

### Number Cards (79 total)
- 0: 1 card
- 1: 1 card
- 2-12: quantity equals face value (2 has 2 cards, 3 has 3 cards, etc.)

### Action Cards (9 total, 3 of each)
- **Freeze**: End target player's turn immediately, lock in their score
- **Flip Three**: Target player draws 3 cards immediately
- **Second Chance**: Target holds card; may discard it plus one duplicate to avoid busting (turn ends)

Action card targeting: Drawer chooses which active player receives effect (may target self). If drawer is only active player, must target self.

### Modifier Cards (6 total)
- **+2, +4, +6, +8, +10** (5 cards): Add value to final score if you don't bust
- **X2** (1 card): Double number card score (applied before modifiers)

## Setup
1. Shuffle all 94 cards
2. Designate dealer (rotates each round)
3. Deal one face-up card to each player
4. Resolve any action cards from initial deal before continuing

## Turn Structure

### Turn Order
Sequential, clockwise from dealer.

### Active Players
Players who have not busted, passed, or been frozen. Only active players can take turns or be targeted by action cards (exception: frozen/passed players can receive Second Chance).

### Player Actions
- **Hit**: Draw top card, add to tableau, check for bust/special effects
- **Pass**: End participation in round, score is calculated and added to total

### Busting
Occurs when two or more cards have the same number. Score 0 for round, discard all cards. Exception: may use Second Chance to avoid.

### Time Limit
Configurable per bot. Exceeding limit = automatic bust, score 0 for round.

## Special Mechanics

### Flip 7 Bonus
Collect exactly 7 unique numbers: turn ends automatically, score normally, receive +15 bonus. Maximum hand size.

### Deck Exhaustion
Shuffle discarded cards from previous rounds (not current tableaus or current round busts) to create new draw pile.

### Action Card Rules

**Freeze**
- Drawer chooses active target
- Target scores current hand immediately
- Target becomes inactive
- Cannot be prevented

**Flip Three**
- Drawer chooses active target
- Target draws 3 cards one at a time (all card types count)
- Stop if player achieves Flip 7 or busts
- Second Chance revealed during Flip Three may be set aside and used immediately
- Other action cards revealed during Flip Three resolve after all 3 cards drawn (if player hasn't busted)
- Target's turn continues after successful resolution (if it's their turn)

**Second Chance**
- Drawer chooses active target
- Target keeps card (placed above number cards)
- Does not count toward 7 numbers
- Limit: one per player (if receiving second, must give to another active player or discard)
- Usage: when receiving duplicate, may discard Second Chance plus duplicate to avoid bust
- Turn ends immediately upon use
- Discarded at end of round even if unused

### Modifier Rules

**+2, +4, +6, +8, +10**
- Keep in tableau
- Do not count toward 7 numbers
- Do not cause busting
- Add value to final score if you don't bust
- Stack (can have multiple)

**X2**
- Keep in tableau
- Does not count toward 7 numbers
- Doubles number card total
- Applied before adding modifiers
- Example: [3,5,7] + [+4] + [X2] = (3+5+7)×2 + 4 = 34

### Tableau Organization
- Number cards (0-12): main area
- Action cards: above number cards
- Modifier cards: with number cards or above

## Scoring

### Round Scoring
If pass or achieve Flip 7 without busting:
1. Sum number cards (including 0)
2. Apply X2 if present
3. Add modifier bonuses (+2, +4, +6, +8, +10)
4. Add +15 if Flip 7 achieved
5. Add to cumulative score

If bust: 0 points for round.

### Game Scoring
- Track cumulative points across rounds
- First to 200+ at round end triggers game end
- If multiple reach 200+ same round, highest total wins
- If tied at 200+, play additional rounds until winner at round end

## Round End
Round ends when all players passed or busted, or only one active player remains and they pass or bust.

At round end:
- Discard all Second Chance cards (even unused)
- Clear all tableaus
- Add cards to discard pile

## Game End
At least one player has 200+ after round completion. Highest score wins.

## Tournament Structure

### Match Format
Best of N (configurable). First to win majority of games wins match.

### Tournament Format
Round robin. Each bot plays every other bot. Players per game configurable. Same time limit for all games.

### Bot Information (Perfect Information)
- All cards in all tableaus
- Complete discard pile
- Remaining deck composition
- All cumulative scores
- Current round number

### Implementation
- Bots inherit from base Bot class
- Must implement: hit/pass decisions, Second Chance usage, action card targeting
- Game history encoded for replay/visualization
- Reference bots: RandomBot, ConservativeBot (passes after 2 cards)
- Invalid moves treated as errors
- Time limit violations = automatic bust

## Sources
- [How to Play Flip 7 | Asmodee](https://www.asmodee.co.uk/blogs/news/how-to-play-flip-7)
- [Flip 7 Rules | Official Game Rules](https://officialgamerules.org/game-rules/flip-7-rules/)
- [Flip 7 | BoardGameGeek](https://boardgamegeek.com/boardgame/420087/flip-7)
- [Board Game Arena - Official Implementation](https://en.boardgamearena.com/doc/Gamehelpflipseven)
- [Flip 7 FAQ - Official](https://flip7scorecard.com/faq/)
- [Geeky Hobbies - Complete Rules Guide](https://www.geekyhobbies.com/flip-7-rules/)
- [Happy Piranha - Official Rules](https://happypiranha.com/blogs/board-game-rules/how-to-play-flip-7-the-greatest-card-game-of-all-time-board-game-rules-instructions)
- [Flip 7 Scoreboard - Detailed Examples](https://flip7scoreboard.com/learn/flip-7-detailed-scoring-examples/)
