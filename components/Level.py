
class Level:
    def __init__(self, current_level=1, current_xp=0, level_up_base=200, level_up_factor=150):

        # TODO: Move defaults to load_functions/InitializeNewGame.py
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor

    @property
    def experience_to_next_level(self):
        # Total XP needed to to next level
        return self.level_up_base + self.current_level * self.level_up_factor

    @property
    def experience_needed_to_next_level(self):
        # XP needed to from current xp to next level
        return self.experience_to_next_level - self.current_xp

    def add_xp(self, xp):
        self.current_xp += xp

        if self.current_xp >= self.experience_to_next_level:
            self.current_xp -= self.experience_to_next_level
            self.current_level += 1

            return True
        else:
            return False