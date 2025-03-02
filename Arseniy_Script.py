import sys
import io
import json
from infinitive import transform
from string import punctuation
from typing import Dict, List, Set, Tuple, Any


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
JSON_FILE = "data/vocab.json"
JSON_INFINITIVE = "data/infinitives.json"
JSON_SYNONYMS = "data/synonyms.json"
JSON_UNIQUE = "data/unique_words.json"
JSON_SAME_ROOTS = "data/sameroots.json"


punctuation = punctuation + "«»" + '"' + '"' + "'" + "-" + "—" + "–"
punctuation_set = set(punctuation)


def process_json(
    input_file: str,
) -> Dict[int, Dict[int, List[str]]]:  # for vocab and uwords
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    organized_data = {}
    for i, chapters in data.items():
        grade = int(i)
        organized_data[grade] = {}
        for j, words in chapters.items():
            chapter = int(j)
            organized_data[grade][chapter] = words
    return organized_data  # type: ignore


def process_json2(
    input_file: str,
) -> Dict[str, List[str]]:  # for synonyms and same roots
    with open(input_file, "r", encoding="utf-8") as file:
        synonyms = json.load(file)
    return synonyms


def build_word_sets(
    organized_data: Dict[int, Dict[int, List[str]]],
    unique_words: Dict[int, Dict[int, List[str]]],
    grade: int,
    section: int,
) -> Tuple[Set[str], Set[str], Set[str]]:  # pre-build sets for better performance
    old_words_set = set[str]()
    for i in range(grade):
        for j, words in organized_data[i].items():
            old_words_set.update(words)
            if j == section:
                break

    new_words_set = set(organized_data[grade][section])
    uwords_set = set(unique_words[grade][section])

    return old_words_set, new_words_set, uwords_set


def Arseniy(text: str) -> None:  # main function - takes text and filters it
    paragraphs = [
        p.strip()
        for p in text.split("\n")
        if p.strip() and not all(c in punctuation_set for c in p)
    ]

    print(f"Total paragraphs found: {len(paragraphs)}")  # Debug print

    with open("data/infinitives.json", "r", encoding="utf-8") as file:
        infs: Dict[str, Any] = json.load(file)
    organized_data: Dict[int, Dict[int, List[str]]] = process_json(JSON_FILE)
    unique_words: Dict[int, Dict[int, List[str]]] = process_json(JSON_UNIQUE)
    synonyms: Dict[str, List[str]] = process_json2(JSON_SYNONYMS)
    same_roots: Dict[str, List[str]] = process_json2(JSON_SAME_ROOTS)

    transformed_cache: Dict[str, List[str]] = {}

    section_headers_written: Dict[int, bool] = {}

    for g, sections in [
        (2, range(1, 8)),
        (3, range(1, 13)),
        (4, range(1, 13)),
        (5, range(1, 13)),
        (6, range(1, 13)),
        (7, range(1, 13)),
    ]:  # now change grade and sections here
        print(f"Processing grade {g}")
        for s in sections:
            print(f"Processing section {s}")
            old_words_set, new_words_set, uwords_set = build_word_sets(
                organized_data, unique_words, g, s
            )

            section_headers_written[s] = False

            max_chunk_paragraphs = 50
            chunks_checked = 0
            chunks_written = 0

            for start in range(len(paragraphs)):
                if start % 100 == 0:
                    print(
                        f"Processing chunks starting at paragraph {start}/{len(paragraphs)}"
                    )

                max_end = min(start + max_chunk_paragraphs, len(paragraphs))

                for end in range(start, max_end):
                    chunks_checked += 1
                    current_chunk = "\n".join(paragraphs[start : end + 1])
                    chunk_words = current_chunk.split()
                    chunk_length = len(chunk_words)

                    if chunk_length > target_len[g - 1][1]:
                        continue

                    if chunk_length < target_len[g - 1][0]:
                        continue

                    meets_criteria, new_words_intext, unique_words_intext = (
                        analyze_chunk(
                            current_chunk,
                            chunk_words,
                            chunk_length,
                            old_words_set,
                            new_words_set,
                            uwords_set,
                            synonyms,
                            same_roots,
                            infs,
                            transformed_cache,
                            g,
                            s,
                        )
                    )

                    if meets_criteria:
                        chunks_written += 1
                        if not section_headers_written[s]:
                            with open(
                                "filtered_chunks.txt", "a", encoding="utf-8"
                            ) as output_file:
                                output_file.write(f"РАЗДЕЛ: {s}\n\n\n\n")
                            section_headers_written[s] = True
                            print(f"found a text for the section: {s}!!!")

                        write_chunk_to_file(
                            current_chunk, new_words_intext, unique_words_intext
                        )

            print(
                f"Section {s} complete. Checked {chunks_checked} chunks, wrote {chunks_written} chunks"
            )


def analyze_chunk(
    chunk: str,
    chunk_words: List[str],
    chunk_length: int,
    old_words_set: Set[str],
    new_words_set: Set[str],
    uwords_set: Set[str],
    synonyms: Dict[str, List[str]],
    same_roots: Dict[str, List[str]],
    infs: Dict[str, Any],
    transformed_cache: Dict[str, List[str]],
    grade: int,
    section: int,
) -> Tuple[bool, Set[str], Set[str]]:  # helper function - analyzes each separate chunk
    transformed_words: List[str] = []

    for word in chunk_words:
        if word in transformed_cache:
            transformed_words.extend(transformed_cache[word])
        else:
            transformed_helper = [
                t.strip()
                for t in transform(word, infs).split("\\~")
                if t.strip() and t not in punctuation_set
            ]
            result = transformed_helper[1::2]
            transformed_cache[word] = result
            transformed_words.extend(result)

    for h, word in enumerate(transformed_words):
        if word in synonyms and word in same_roots and word not in uwords_set:
            good_synonyms = ""
            good_same_roots = ""

            for synonym in synonyms[word]:
                if synonym in new_words_set:
                    good_synonyms += "!" + synonym

            for same_root in same_roots[word]:
                if same_root in new_words_set:
                    good_same_roots += "#" + same_root

            if good_synonyms or good_same_roots:
                transformed_words[h] = good_synonyms + good_same_roots

    unknown_words = sum(1 for word in transformed_words if word not in old_words_set)
    unknown_per = unknown_words / chunk_length

    new_words_intext: Set[str] = set()
    unique_words_intext: Set[str] = set()
    for word in transformed_words:
        if word in new_words_set:
            new_words_intext.add(word)
        if word in uwords_set:
            unique_words_intext.add(word)
    new_words_cov = len(new_words_intext)
    unique_words_cov = len(unique_words_intext)

    meets_criteria = (
        unknown_per < 1 and new_words_cov > 3 and unique_words_cov >= 0
    )  # benchmarks

    return meets_criteria, new_words_intext, unique_words_intext


def write_chunk_to_file(
    chunk: str, new_words_intext: Set[str], unique_words_intext: Set[str]
) -> None:  # write chunk to file
    with open("filtered_chunks.txt", "a", encoding="utf-8") as output_file:
        output_file.write(
            chunk
            + "\n\n"
            + "Количество новых слов: "
            + str(len(new_words_intext))
            + " | "
            + "Новые слова: "
            + ", ".join(new_words_intext)
            + "\nКоличество уникальных слов: "
            + str(len(unique_words_intext))
            + " | "
            + "Уникальные слова: "
            + ", ".join(unique_words_intext)
            + "\n"
            + ("-" * 10)
            + "\n\n"
        )


def main() -> None:
    with open(TXT_FILE, "r", encoding="utf-8") as txt_file:
        text = txt_file.read()

    with open("filtered_chunks.txt", "w", encoding="utf-8"):
        pass

    Arseniy(text)


if __name__ == "__main__":
    main()
