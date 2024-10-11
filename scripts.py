def open_file(file):
    with open(file, "r", encoding="KOI8-R") as my_file:
        file_contents = my_file.read()
    return file_contents


def parse_questions(file_contents):
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



def main():
    file_contents = open_file("questions/1vs1200.txt")
    quiz_dict = parse_questions(file_contents)

    print(quiz_dict)


if __name__ == "__main__":
    main()