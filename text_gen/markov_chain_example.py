import markovify


def markov_chain():
    # Get raw text as string.
    with open("./data/corpora/text_1.txt", encoding='utf8') as f:
        text = f.read()

    # Build the model.
    text_model = markovify.Text(text)

    # Print five randomly-generated sentences
    print('\n\n---Print five randomly-generated sentences---')
    for i in range(5):
        print()
        print(text_model.make_sentence())

    # Print three randomly-generated sentences of no more than 280 characters
    print('\n\n---Print three randomly-generated sentences of no more than 280 characters---')
    for i in range(3):
        print()
        print(text_model.make_short_sentence(280))

markov_chain()