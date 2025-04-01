from roles._role import Role


class Werewolf(Role):
    """Werewolf player class."""

    def __init__(self, model_config: dict[str, str], id: int):
        super().__init__(model_config, id)
        self.role = "werewolf"
        self.system_prompt += """
        You've checked your card and found out that you have the role of: werewolf.

        Tips:
        - Make sure to blend in and not attract suspicion
        - Pretend you're another role and that you're helping out the villagers
        """
