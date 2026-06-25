from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class SM2State:
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_date: date


def review(
    ease_factor: float,
    interval_days: int,
    repetitions: int,
    quality: int,  # 0-5
) -> SM2State:
    """
    Apply one SM-2 review step.
    quality: 0=complete blackout, 1=wrong, 2=wrong but familiar,
             3=correct with difficulty, 4=correct, 5=perfect
    """
    if quality < 3:
        # Reset
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = repetitions + 1
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval_days * ease_factor)

    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)

    return SM2State(
        ease_factor=round(new_ef, 4),
        interval_days=new_interval,
        repetitions=new_repetitions,
        next_review_date=date.today() + timedelta(days=new_interval),
    )
