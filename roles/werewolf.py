from roles._role import Role


class Werewolf(Role):
    """Werewolf player class."""

    def __init__(self, model_config: dict[str, str], id: int):
        super().__init__(model_config, id)
        self.role = "werewolf"
        self.system_prompt += "\nYou've checked your card and found out that you have the role of: werewolf."
