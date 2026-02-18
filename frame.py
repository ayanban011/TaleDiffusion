from character import CharacterMoment


class Frame:
    def __init__(self, scene_description, characters: list[CharacterMoment]):
        self.scene_description = scene_description
        self.character_moments = characters

    def __str__(self):
        out = f"Scene: {self.scene_description}\n"
        out += "Characters:\n"
        for character in self.character_moments:
            out += character.__str__() + "\n"
        return out

    def to_dict(self):
        return {
            "scene_description": self.scene_description,
            "character_moments": [character.to_dict() for character in self.character_moments]
        }
