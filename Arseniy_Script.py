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

    organized_data: Dict[int, Dict[int, List[str]]] = {}
    for i, chapters in data.items():
        grade = int(i)
        organized_data[grade] = {}
        for j, words in chapters.items():
            chapter = int(j)
            organized_data[grade][chapter] = words
    return organized_data


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
    # Build old_words_set from all words in previous grades and sections
    old_words_set: Set[str] = set()

    # Add words from all previous grades
    for g in range(1, grade):
        if g in organized_data:
            for s in organized_data[g]:
                old_words_set.update(organized_data[g][s])

    # Add words from current grade up to the current section
    if grade in organized_data:
        for s in range(1, section):
            if s in organized_data[grade]:
                old_words_set.update(organized_data[grade][s])

    # Get new words for the current grade and section
    new_words_set: Set[str] = set()
    if grade in organized_data and section in organized_data[grade]:
        new_words_set = set(organized_data[grade][section])

    # Get unique words for the current grade and section
    uwords_set: Set[str] = set()
    if grade in unique_words and section in unique_words[grade]:
        uwords_set = set(unique_words[grade][section])

    return old_words_set, new_words_set, uwords_set


def Arseniy(text: str) -> None:  # main function - takes text and filters it
    # Filter paragraphs more efficiently
    paragraphs: List[str] = []
    for p in text.split("\n"):
        p_stripped = p.strip()
        if p_stripped and not all(c in punctuation_set for c in p_stripped):
            paragraphs.append(p_stripped)

    print(f"Total paragraphs found: {len(paragraphs)}")

    # Load all data at once
    with open("data/infinitives.json", "r", encoding="utf-8") as file:
        infs: Dict[str, Any] = json.load(file)
    organized_data: Dict[int, Dict[int, List[str]]] = process_json(JSON_FILE)
    unique_words: Dict[int, Dict[int, List[str]]] = process_json(JSON_UNIQUE)
    synonyms: Dict[str, List[str]] = process_json2(JSON_SYNONYMS)
    same_roots: Dict[str, List[str]] = process_json2(JSON_SAME_ROOTS)

    # Initialize caches
    transformed_cache: Dict[str, List[str]] = {}

    # Pre-cache paragraph words to avoid repeated splitting
    paragraph_words_cache: List[List[str]] = [p.split() for p in paragraphs]
    paragraph_lengths: List[int] = [len(words) for words in paragraph_words_cache]

    section_headers_written: Dict[int, bool] = {}

    for g, sections in [
        (2, range(1, 9)),
        (3, range(1, 9)),
        (4, range(1, 9)),
        (5, range(1, 14)),
        (6, range(1, 16)),
        (7, range(1, 14)),
        (8, range(1, 14)),
    ]:  # now change grade and sections here, IMPORTANT: WRITE LAST SECTION # + 1
        print(f"Processing grade {g}")

        # Pre-build word sets for each grade to avoid rebuilding for each section
        grade_word_sets: Dict[int, Tuple[Set[str], Set[str], Set[str]]] = {}
        for s in sections:
            grade_word_sets[s] = build_word_sets(organized_data, unique_words, g, s)

        for s in sections:
            print(f"Processing section {s}")
            old_words_set, new_words_set, uwords_set = grade_word_sets[s]

            section_headers_written[s] = False

            max_chunk_paragraphs = 50
            chunks_checked = 0
            chunks_written = 0

            # Pre-compute target length for this grade
            min_target_len, max_target_len = target_len[g - 1]

            for start in range(len(paragraphs)):
                if start % 500 == 0:
                    print(
                        f"Processing chunks starting at paragraph {start}/{len(paragraphs)}"
                    )

                # Use the simpler approach from the original code that considers more chunks
                max_end = min(start + max_chunk_paragraphs, len(paragraphs))

                for end in range(start, max_end):
                    chunks_checked += 1

                    # Calculate chunk length without joining and splitting again
                    chunk_length = sum(paragraph_lengths[start : end + 1])

                    if chunk_length > max_target_len:
                        continue
                    if chunk_length < min_target_len:
                        continue

                    # Only create the chunk if it passes initial length checks
                    current_chunk = "\n".join(paragraphs[start : end + 1])

                    # Use pre-cached words instead of splitting again
                    chunk_words: List[str] = []
                    for i in range(start, end + 1):
                        chunk_words.extend(paragraph_words_cache[i])

                    (
                        meets_criteria,
                        new_words_intext,
                        unique_words_intext,
                        modified_chunk,
                    ) = analyze_chunk(
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
                    if meets_criteria:
                        chunks_written += 1
                        if not section_headers_written[s]:
                            section_headers_written[s] = True
                            print(f"found a text for the section: {s}!!!")
                        write_chunk_to_file(
                            modified_chunk, new_words_intext, unique_words_intext
                        )
            print(f"Section {s} complete. Wrote {chunks_written} chunks")


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
) -> Tuple[bool, Set[str], Set[str], str]:
    # The original function with set operations for efficiency
    transformed_words: List[str] = []
    word_positions: Dict[str, List[int]] = {}

    # Process all words in the chunk
    for i, word in enumerate(chunk_words):
        if word not in word_positions:
            word_positions[word] = []
        word_positions[word].append(i)

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

    for word in word_positions:
        if word in transformed_cache:
            word_transforms = transformed_cache[word]
            for transform_word in word_transforms:
                good_synonyms = ""
                good_same_roots = ""
                synonym_words: List[str] = []
                same_root_words: List[str] = []
                if transform_word in synonyms:
                    for synonym in synonyms[transform_word]:
                        if synonym in new_words_set:
                            good_synonyms += "!" + synonym
                            synonym_words.append(synonym)
                if transform_word in same_roots:
                    for same_root in same_roots[transform_word]:
                        if same_root in new_words_set:
                            good_same_roots += "#" + same_root
                            same_root_words.append(same_root)
                if good_synonyms or good_same_roots:
                    for pos in word_positions[word]:
                        chunk_words[pos] = f"{word} ({good_synonyms}{good_same_roots})"
                    transformed_words.extend(synonym_words)
                    transformed_words.extend(same_root_words)

    modified_chunk = " ".join(chunk_words)

    transformed_words_set = set(transformed_words)
    unknown_words = len(transformed_words_set - old_words_set)
    unknown_per = unknown_words / chunk_length

    new_words_intext = transformed_words_set.intersection(new_words_set)
    unique_words_intext = transformed_words_set.intersection(uwords_set)

    new_words_cov = len(new_words_intext)
    unique_words_cov = len(unique_words_intext)

    criteria1 = unknown_per < 1
    criteria2 = new_words_cov > 3
    criteria3 = unique_words_cov >= 0

    meets_criteria = criteria1 and criteria2 and criteria3

    return meets_criteria, new_words_intext, unique_words_intext, modified_chunk


def write_chunk_to_file(
    chunk: str, new_words_intext: Set[str], unique_words_intext: Set[str]
) -> None:  # write chunk to file
    with open("filtered_chunks.txt", "a", encoding="utf-8") as output_file:
        output_file.write(
            chunk
            + "\n\n"
            + "Количество новых слов: "
            + str(len(new_words_intext))
            + "\nНовые слова: "
            + ", ".join(new_words_intext)
            + "\nКоличество уникальных слов: "
            + str(len(unique_words_intext))
            + "\nУникальные слова: "
            + ", ".join(unique_words_intext)
            + "\n"
            + ("-" * 10)
            + "\n\n"
        )


def main() -> None:
    with open(TXT_FILE, "r", encoding="utf-8") as txt_file:
        text = txt_file.read()

    # Create or clear the output file with a valid, safe filename
    output_filename = "filtered_chunks.txt"
    with open(output_filename, "w", encoding="utf-8") as _:
        pass

    Arseniy(text)


if __name__ == "__main__":
    main()
