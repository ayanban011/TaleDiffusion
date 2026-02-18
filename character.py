class Character:
    def __init__(self, name, physical_description, personality):
        self.name = name
        self.physical_description = physical_description
        self.personality = personality

    def __str__(self):
        return f"Name: {self.name}\nPhysical Description: {self.physical_description}\nPersonality: {self.personality}"

    def to_dict(self):
        return {
            "name": self.name,
            "physical_description": self.physical_description,
            "personality": self.personality
        }


class CharacterMoment(Character):
    def __init__(self, base_character: Character, action: str, dialogue: str):
        super().__init__(base_character.name, base_character.physical_description, base_character.personality)
        self.action = action
        self.dialogue = dialogue

    def __str__(self):
        return f"{super().__str__()}\nAction: {self.action}\nDialogue: {self.dialogue}"

    def no_dialogue_description(self):
        return f"{super().__str__()}\nAction: {self.action}"

    def to_dict(self):
        return {
            "name": self.name,
            "physical_description": self.physical_description,
            "personality": self.personality,
            "action": self.action,
            "dialogue": self.dialogue
        }
