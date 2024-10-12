def parse_questions(file):
    with open(file, "r", encoding="KOI8-R") as file:
        file_contents = file.read()
    questions_and_answers = {}
    sections = file_contents.split('\n\n')
    question = None
    answer = None

    for line in sections:
        if line.startswith('Вопрос'):
            question = ' '.join(line.split()[2:])
        elif line.startswith('Ответ'):
            answer = line.replace('\n', ' ').lstrip(' Ответ:').rstrip('.')
        if question and answer:
            questions_and_answers[question] = answer
    return questions_and_answers
