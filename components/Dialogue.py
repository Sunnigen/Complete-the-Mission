from random import choice


class Dialogue:

    def __init__(self, dialogue_options):
        self.dialogue_options = dialogue_options
        self.current_dialogue_index = -1

    def interact(self, entity):
        pass

    def initiate_dialogue(self):
        self.current_dialogue_index = 0
        return self.dialogue_options[0]

    def continue_dialogue(self):
        self.current_dialogue_index += 1
        if self.current_dialogue_index >= len(self.dialogue_options):
            self.current_dialogue_index = 0
            return []
        return self.dialogue_options[self.current_dialogue_index]
