from roles._role import Role


class Villager(Role):
    """Villager player class."""

    def __init__(self, model_config: dict[str, str], id: int):
        super().__init__(model_config, id)
        self.role = "villager"
        self.system_prompt += """
        You've checked your card and found out that you have the role of: villager.

        Tips:
        - Work with others to identify the werewolf/werewolves
        - Establish people's roles and try to find inconsistencies
        """
