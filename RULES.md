# Flip 7 Tournament Rules

## Game Objective
Be the first player to reach **200 points** across multiple rounds. Each round, players draw cards trying to collect up to 7 unique numbers without busting.

## Deck Composition
The deck contains **94 cards total**:

### Number Cards
- One 1 card
- Two 2 cards
- Three 3 cards
- Four 4 cards
- Five 5 cards
- Six 6 cards
- Seven 7 cards
- Eight 8 cards
- Nine 9 cards
- Ten 10 cards
- Eleven 11 cards
- Twelve 12 cards
- One 0 card

**Total: 79 number cards**

### Action Cards (9 cards total - 3 of each type)
- **Freeze** (3 cards): Immediately end the target player's turn and lock in their current score
- **Flip Three** (3 cards): Target player draws 3 cards from the top of the deck immediately
- **Second Chance** (3 cards): Target player holds this card. When they would bust, they may discard it along with one duplicate to avoid busting (but their turn ends immediately)

**Action Card Targeting:**
- When ANY player draws an action card (including during initial deal), that player immediately chooses which active player receives the card's effect (they may choose themselves or any other active player)
- If the drawer is the only active player, they MUST play the action card on themselves
- Action cards are placed ABOVE your number cards in your tableau (physical card organization)

### Modifier Cards (6 cards total)
- **+2, +4, +6, +8, +10** (5 cards - one of each): Add the shown value to your final score for the round (if you don't bust)
- **X2** (1 card): Double your score from number cards (applied before adding modifier bonuses)

## Setup
1. Shuffle all 94 cards to form the central draw pile
2. Designate a dealer (role rotates each round)
3. Dealer deals one card face-up to each player
4. If any player receives an action card during initial deal, resolve it before continuing

## Round Structure

### Initial Deal
Each player receives one face-up card to start the round. If an action card is dealt during initial deal:
- The player who received the action card immediately chooses who gets the effect (themselves or another player)
- **Freeze**: Chosen player immediately passes for the round
- **Flip Three**: Chosen player receives 3 additional cards immediately
- **Second Chance**: Chosen player keeps it in hand for later use
- **Modifier cards**: Player who was dealt it keeps it as part of their tableau

### Turn Order
Players take turns **sequentially** in clockwise order from the dealer.

### Tableau Organization
When organizing cards in your tableau:
- **Number cards** (0-12): Placed in the main area
- **Action cards** (Freeze, Flip Three, Second Chance): Placed ABOVE your number cards
- **Modifier cards** (+2, +4, +6, +8, +10, X2): Placed with number cards or above as preferred
- This organization helps visually distinguish between card types during gameplay

### Active Players
A player is considered **active** if they have NOT:
- Busted in the current round
- Passed (decided to stay) in the current round
- Been frozen by a Freeze action card in the current round

Only active players can:
- Take turns (hit or pass)
- Be targeted by action cards (with the exception of frozen/passed players who can still receive Second Chance for future rounds)

### On Your Turn
You have two options:

1. **Hit**: Draw the top card from the deck
   - Add it to your tableau face-up
   - Check if you busted (see Busting below)
   - Check for special card effects

2. **Pass** (also called **Stay**): End your participation in this round
   - You are no longer an active player for this round
   - Your score is calculated and added to your total
   - You wait for other players to finish the round
   - You will participate in the next round normally

### Busting
You **bust** when you have **two or more cards with the same number** in your tableau at the same time.

When you bust:
- You score **0 points** for the round
- All your cards are discarded
- You wait for the round to end
- Exception: You may use a Second Chance card to prevent the bust (see below)

### Turn Time Limit
- Each bot has a **configurable time limit** (set in constants file) to make their decision
- If a bot exceeds the time limit, they **automatically bust** and score 0 for the round

## Special Mechanics

### Flip 7 Bonus
If you collect exactly **7 unique numbers** (no duplicates):
- You immediately end your turn (automatically pass)
- You score your cards normally
- You receive a **+15 bonus** added to your round score
- This is the maximum hand size possible

### Deck Exhaustion
If the draw pile runs out during a round:
- Shuffle all discarded cards from previous rounds to create a new draw pile
- Do NOT shuffle cards currently in player tableaus
- Do NOT shuffle cards discarded from busts in the current round

### Action Card Details

#### Freeze
- **Targeting:** When drawn, the drawer immediately chooses which active player receives this effect (may choose themselves)
- The target player banks all the points they have collected
- The target player is out of the round (no longer active)
- Target player scores their current hand
- Cannot be prevented or delayed

#### Flip Three
- **Targeting:** When drawn, the drawer immediately chooses which active player receives this effect (may choose themselves)
- Target player must accept the next 3 cards, flipping them one at a time
- **ALL card types count toward the 3 cards:** number cards, action cards, AND modifier cards
- **Stop conditions:** Regardless of how many cards remain to flip, STOP if:
  - The player achieves Flip 7 (7 unique number cards), OR
  - The player busts
- **Special card handling during Flip Three:**
  - If a **Second Chance** card is revealed during Flip Three, it may be set aside and used immediately if needed
  - If another **Flip Three** or **Freeze** card is revealed during Flip Three, they are resolved AFTER all 3 cards are drawn (but only if the player hasn't busted)
- Normal busting rules apply to each card drawn
- If the target player busts during Flip Three (and doesn't/can't use Second Chance), they stop drawing immediately and do not draw the remaining cards
- After successfully resolving all 3 cards without busting, if it's the target player's turn, their turn continues (they can hit or pass)

#### Second Chance
- **Targeting:** When drawn, the drawer immediately chooses which active player receives this card (may choose themselves)
- Target player keeps this card in front of them (set above their number cards)
- Does NOT count as one of the 7 numbers
- **Holding Limit:** A player may only have ONE Second Chance in front of them at a time. If a player would receive a second Second Chance, they must immediately choose another active player to give it to. If there are no other active players OR if everyone else already has one, then discard the Second Chance card
- **Usage:** When a player is given a card with a duplicate number:
  - The bot decides whether to use their Second Chance
  - If used: Discard the Second Chance card AND the duplicate number card
  - The player does NOT bust
  - **CRITICAL:** The player's turn ends immediately - they cannot continue drawing cards
  - The player scores their remaining cards normally
- Can only be used when you would bust from a duplicate
- **End of Round:** All Second Chance cards are discarded at the end of a round even if they were never used. This includes cases where:
  - The player who drew it got a Freeze card played on them
  - The player successfully achieved Flip 7
  - The player passed without needing to use it

### Modifier Card Details

#### +2, +4, +6, +8, +10 Modifiers
- Keep in your tableau when drawn
- Do NOT count as one of your 7 numbers
- Do NOT cause busting
- Add the shown value to your final score IF you don't bust
- Multiple modifier cards stack (you can have +2, +4, +6 all at once)

#### X2 (Double)
- Keep in your tableau when drawn
- Do NOT count as one of your 7 numbers
- Doubles the point value of all your number cards
- Applied BEFORE adding +2, +4, +6, +8, +10 modifiers
- Example: You have [3, 5, 7] + [+4] + [X2]
  - Number cards total: 3 + 5 + 7 = 15
  - After X2: 15 × 2 = 30
  - After +4 modifier: 30 + 4 = 34 final score

## Scoring

### Round Scoring
If you **pass** or achieve **Flip 7 bonus** without busting:

1. Sum all your number cards (including the 0 card if present)
2. If you have an X2 modifier, double this sum
3. Add all +2, +4, +6, +8, +10 modifier bonuses
4. If you achieved Flip 7 bonus (7 unique numbers), add +15
5. Add this total to your cumulative score

If you **bust**:
- Score 0 for the round regardless of cards

### Game Scoring
- Track cumulative points across all rounds
- First player to reach **200 or more points** at the end of any round triggers game end
- If multiple players reach 200+ in the same round, highest total wins
- If tied at 200+, continue playing additional rounds until one player has a higher score at the end of any round

## Tournament Structure

### Match Format
- Games are played **Best of N** (configurable, e.g., Best of 3, Best of 5)
- Each individual game is played until at least one player reaches 200 points
- First bot to win the majority of games wins the match

### Tournament Format
- **Round Robin**: Each bot plays against every other bot
- Number of players per game is **configurable**
- All games use the same time limit settings from the constants file

### Bot Information Access
Bots have **perfect information**:
- See all cards in all players' tableaus
- Know the complete discard pile
- Can calculate remaining deck composition
- See all players' cumulative scores
- Know the current round number

### Timing and Validation
- Bots must complete their decision within the configured time limit
- Exceeding the time limit results in an automatic bust for that round
- Invalid moves are treated as errors (implementation should prevent these)

## Round End Conditions
A round ends when:
- All players have either passed or busted, OR
- Only one player remains active (others passed/busted), AND that player decides to pass or bust

**At the end of each round:**
- All Second Chance cards are discarded (even unused ones)
- All cards are cleared from player tableaus
- Discard pile accumulates

## Game End Conditions
A game ends when:
- At least one player has 200+ points after a round completes
- The player with the highest score wins that game

## Tournament Notes
- Bots are implemented as Python classes inheriting from a base Bot class
- Bots must implement decision methods for:
  - Hit or Pass decisions
  - Second Chance usage decisions
  - Any other action card decisions as they arise
- Game history is encoded for replay/visualization
- Reference bots provided: RandomBot, ConservativeBot (always passes after 2 cards)

## Sources
- [How to Play Flip 7 | Asmodee](https://www.asmodee.co.uk/blogs/news/how-to-play-flip-7)
- [Flip 7 Rules | Official Game Rules](https://officialgamerules.org/game-rules/flip-7-rules/)
- [Flip 7 | BoardGameGeek](https://boardgamegeek.com/boardgame/420087/flip-7)
- [Board Game Arena - Official Implementation](https://en.boardgamearena.com/doc/Gamehelpflipseven)
- [Flip 7 FAQ - Official](https://flip7scorecard.com/faq/)
- [Geeky Hobbies - Complete Rules Guide](https://www.geekyhobbies.com/flip-7-rules/)
- [Happy Piranha - Official Rules](https://happypiranha.com/blogs/board-game-rules/how-to-play-flip-7-the-greatest-card-game-of-all-time-board-game-rules-instructions)
- [Flip 7 Scoreboard - Detailed Examples](https://flip7scoreboard.com/learn/flip-7-detailed-scoring-examples/)
