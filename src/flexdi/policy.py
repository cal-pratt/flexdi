from dataclasses import dataclass


@dataclass
class FlexPolicy:
    eager: bool


DEFAULT_POLICY = FlexPolicy(eager=False)
