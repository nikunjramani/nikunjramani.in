from src.contact.spam import score_spam


def test_empty_message_scores_zero() -> None:
    assert score_spam("") == 0.0


def test_ordinary_message_scores_low() -> None:
    assert score_spam("Hi, I really liked your inventory sync write-up. Nice work!") < 0.3


def test_many_links_scores_high() -> None:
    spam = "check https://a.com and https://b.com and www.c.com and http://d.com now"
    assert score_spam(spam) >= 0.6


def test_shouting_scores_up() -> None:
    shouting = "BUY NOW THE BEST DEAL EVER AVAILABLE TODAY ONLY CLICK HERE FAST"
    assert score_spam(shouting) > 0.0


def test_repeated_characters_score_up() -> None:
    assert score_spam("hellooooooooooo there") > 0.0


def test_score_never_exceeds_one() -> None:
    # Deliberately trips all three signals at once: uppercase links satisfy both the
    # link-count and all-caps-ratio checks without lowercase URL text diluting the
    # letter ratio, plus a run of the same repeated character.
    worst = ("HTTPS://A.COM " * 15) + "AAAAAAAAAAAAAAA"
    assert score_spam(worst) == 1.0
