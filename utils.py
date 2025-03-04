import random
from collections import Counter


def count_votes(votes: list[int]) -> int:
    # Check the votes and announce the results
    vote_count = Counter(votes)
    top_voted_players = [player for player, count in vote_count.items() if count == max(vote_count.values())]
    print(f"Vote results: {', '.join([f'Player {player} ({count} votes)' for player, count in vote_count.items()])}")

    if len(top_voted_players) > 1:
        print("There was a tie for the most votes. The elimination will be decided by a random draw.")
        eliminated_player = random.choice(top_voted_players)
    else:
        eliminated_player = top_voted_players[0]
        print(f"Player {eliminated_player} has the most votes.")

    return eliminated_player
