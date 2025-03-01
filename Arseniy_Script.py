import sys
import io
import json
from infinitive import transform, GuessOptions
from string import punctuation


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

target_len = [
    (10, 100),
    (60, 130),
    (60, 250),
    (60, 300),
    (60, 350),
    (60, 415),
    (60, 500),
    (60, 550),
    (60, 700),
    (60, 750),
    (60, 800),
]  # здесь можно менять числа
TXT_FILE = "testtext.txt"
JSON_FILE = "jsons/vocab.json"
JSON_INFINITIVE = "infinitives.json"
JSON_SYNONYMS = "jsons/synonyms.json"
JSON_UNIQUE = "jsons/unique_words.json"
JSON_SAME_ROOTS = "jsons/sameroots.json"


punctuation = punctuation + "«»" + '"' + "”" + "“" + "“" + "”" + "—" + "–"


def process_json(input_file: str) -> dict[int, dict[int, list[str]]]:
    organized_data = {}
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    for i, chapters in data.items():
        grade = int(i)
        organized_data[grade] = {}
        for j, words in chapters.items():
            chapter = int(j)
            organized_data[grade][chapter] = words
    return organized_data  # type: ignore


def process_synonyms(input_file: str) -> dict[str, list[str]]:
    with open(input_file, "r", encoding="utf-8") as file:
        synonyms = json.load(file)
    return synonyms


def Arseniy(text: str):
    paragraphs = text.split("\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip() and p not in punctuation]
    with open("infinitives.json", "r", encoding="utf-8") as file:
        infs = json.load(file)
    organized_data = process_json(JSON_FILE)
    synonyms = process_synonyms(JSON_SYNONYMS)
    same_roots = process_synonyms(JSON_SAME_ROOTS)

    unique_words = process_json(JSON_UNIQUE)

    for start in range(len(paragraphs)):
        current_chunk = ""
        for end in range(start, len(paragraphs)):
            current_chunk = "\n".join(paragraphs[start : end + 1])
            for g, sections in [(5, range(1, 13))]: # now change grade and sections here
                if len(current_chunk.split()) > target_len[g - 1][1]:
                    break
                elif len(current_chunk.split()) < target_len[g - 1][0]:
                    continue
                for s in sections:
                    analyze_chunk(
                        current_chunk,
                        organized_data,
                        unique_words,
                        synonyms,
                        same_roots,
                        infs,
                        g,
                        s,
                    )


def analyze_chunk(
    chunk: str,
    organized_data: dict[int, dict[int, list[str]]],
    unique_words: dict[int, dict[int, list[str]]],
    synonyms: dict[str, list[str]],
    same_roots: dict[str, list[str]],
    infs: dict[str, GuessOptions],
    grade: int,
    section: int,
):
    chunk_length = len(chunk.split())
    words_in_chunk = chunk.split()
    transformed_words = list[str]()
    for i, word in enumerate(words_in_chunk):
        transformed_helper = [
            t.strip()
            for t in transform(word, infs).split("\\~")
            if t.strip() and t not in punctuation
        ]
        transformed_words.extend(transformed_helper[1::2])
    print(transformed_words)

    old_words = list[str]()
    for i in range(grade):
        for j, words in organized_data[i].items():
            old_words.extend(words)
            if j == section:
                break
    new_words = organized_data[grade][section]
    uwords = unique_words[grade][section]

    for h, word in enumerate(transformed_words):
        if word in synonyms and word in same_roots and word not in uwords:
            good_synonyms = str()
            good_same_roots = str()
            for synonym in synonyms[word]:
                if synonym in new_words:
                    good_synonyms += "!" + synonym
            for same_root in same_roots[word]:
                if same_root in new_words:
                    good_same_roots += "#" + same_root
            if good_synonyms or good_same_roots:
                transformed_words[h] = good_synonyms + good_same_roots
        else:
            continue

    new_words_intext = set[str]()
    unique_words_intext = set[str]()

    unknown_per = (
        sum(1 for word in transformed_words if word not in old_words) / chunk_length
    )
    for word in transformed_words:
        if word in new_words:
            new_words_intext.add(word)
        if word in uwords:
            unique_words_intext.add(word)
    new_words_cov = len(new_words_intext)
    unique_words_cov = len(unique_words_intext)
    print(unknown_per)
    print(new_words_cov)
    print(unique_words_cov)

    if unknown_per < 1 and new_words_cov > 3 and unique_words_cov >= 0:  # benchmarks
        with open("filtered_chunks.txt", "a", encoding="utf-8") as output_file:
            output_file.write(
                chunk
                + "\n\n"
                + "Количество новых слов: "
                + str(new_words_cov)
                + "\nНовые слова: "
                + ", ".join(new_words_intext)
                + "\nКоличество уникальных слов: "
                + str(unique_words_cov)
                + "\nУникальные слова: "
                + ", ".join(unique_words_intext)
                + "\n"
                + ("-" * 10)
                + "\n\n"
            )


def main():
    with open(TXT_FILE, "r", encoding="utf-8") as txt_file:
        text = txt_file.read()
    with open("filtered_chunks.txt", "w", encoding="utf-8") as _:
        pass

    Arseniy(text)

    with open("filtered_chunks.txt", "r", encoding="utf-8") as filtered_file:
        filtered_content = filtered_file.read()
    print("Filtered Chunks:")
    print(filtered_content)


if __name__ == "__main__":
    main()
