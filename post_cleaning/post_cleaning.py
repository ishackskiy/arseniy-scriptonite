import json

# read processed data after Arseniy_Script.py
def read_and_split_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split content based on '----------'
    chunks = [chunk.strip().split('\n') for chunk in content.split('----------') if chunk.strip()]

    return chunks

# 2 comparing functions for deciding whether to combine chunks or not
def compare_chunks(chunk1, chunk2):
    lines1 = []
    lines2 = []
    for i in range(chunk1[0]):
        lines1.append(chunk1[i + 1])
    for i in range(chunk2[0]):
        lines2.append(chunk2[i + 1])
    return bool(set(lines1) & set(lines2))

def compare_new_words(chunk1, chunk2):
    new_words1 = chunk1[chunk1[0] + 1]
    new_words2 = chunk2[chunk2[0] + 1]
    return bool(set(new_words1) & set(new_words2))

# additional filtering based on new words
def filter_new(array, target):
    output = []
    for i in range(len(array)):
        if len(array[i][-4]) >= target:
            output.append(array[i])
    
    return output

# additional filtering based on unique words
def filter_unique(array, target):
    output = []
    for i in range(len(array)):
        if len(array[i][-3]) >= target:
            output.append(array[i])
    
    return output

# put the processed data into an array of processed chunks - pchunks
filename = "post_cleaning/post_cleaning.txt"
chunks = read_and_split_file(filename)
pchunks = []

for i in range(len(chunks)):
    processed_ch = []
    counter = 0
    new_words = []
    new_unique_words = []
    while chunks[i][counter] != '':
        processed_ch.append(chunks[i][counter])
        counter += 1
    processed_ch.insert(0, counter)
    chunks[i][counter + 2] = chunks[i][counter + 2][chunks[i][counter + 2].find(":") + 2:]
    new_words = chunks[i][counter + 2].split(', ')
    chunks[i][counter + 4] = chunks[i][counter + 4][chunks[i][counter + 4].find(":") + 2:]
    new_unique_words = chunks[i][counter + 4].split(', ')
    processed_ch.append(new_words)
    processed_ch.append(new_unique_words)
    pchunks.append(processed_ch)

# combine chunks and put them into an array of excerpts with some addtional info - excerpts
ocounter = 0
excerpts = []
while ocounter < len(pchunks):
    icounter = 0
    combined_chunk = pchunks[ocounter + icounter]
    while ocounter + icounter + 1 < len(pchunks) and compare_chunks(combined_chunk, pchunks[ocounter + icounter + 1]) and compare_new_words(combined_chunk, pchunks[ocounter + icounter + 1]):
        num_lines = combined_chunk[0]
        for i in range(pchunks[ocounter + icounter + 1][0]):
            if not pchunks[ocounter + icounter + 1][i + 1] in combined_chunk:
                combined_chunk.insert(num_lines + 1, pchunks[ocounter + icounter + 1][i + 1])
                num_lines = num_lines + 1
        combined_chunk[0] = num_lines
        combined_chunk[-2] = list(set(combined_chunk[-2] + pchunks[ocounter + icounter + 1][-2]))
        combined_chunk[-1] = list(set(combined_chunk[-1] + pchunks[ocounter + icounter + 1][-1]))
        icounter = icounter + 1
    excerpts.append(combined_chunk)
    ocounter = ocounter + icounter + 1

print(len(pchunks))
# add info about grade and section for each excerpt
with open("jsons/vocab.json", 'r', encoding='utf-8') as file:
    file = json.load(file)
    for i in range(len(excerpts)):
        all_locations = []
        for j in range(len(excerpts[i][-2])):
            possible_locations = []
            for grade in file:
                for section in file[grade]:
                    if excerpts[i][-2][j] in file[grade][section]:
                        possible_locations.append((grade, section))
            all_locations.append(possible_locations)

        common = set(all_locations[0])
        for arr in all_locations[1:]:
            common = common.intersection(set(arr))

        excerpts[i].append(list(common)[0][0])
        excerpts[i].append(list(common)[0][1])

# delete excerpts for the grade 0 (this is a grade where we put the very basic words that are not anywhere in the program of MON for an unknown reason)
filtered_excerpts = []
counter = 0
while counter < len(excerpts):
    if excerpts[counter][-2] != 0:
        filtered_excerpts.append(excerpts[counter])
        counter = counter + 1
    else:
        counter = counter + 1

# additional filtering based on unique and new words
filtered_excerpts = filter_new(filtered_excerpts, 6)
filtered_excerpts = filter_unique(filtered_excerpts, 0)

# make the empty lists of unique words really empty (otherwise they are arrays with a single elemnet of '' (empty string))
for i in range(len(filtered_excerpts)):
    if filtered_excerpts[i][-3] == ['']:
        filtered_excerpts[i][-3] = []

# order the excerpts based on subsections
filtered_excerpts.sort(key=lambda x: x[-1])

# print the post-cleaned data into to_NE.txt and print the number of excerpts in the terminal
with open("potential_chunks/to_NE.txt", "w", encoding="utf-8") as output_file:
    output_file.write("")
for i in range(len(filtered_excerpts)):
    text = ''
    for j in range(filtered_excerpts[i][0]):
        text = text + filtered_excerpts[i][j + 1]
    with open("potential_chunks/to_NE.txt", "a", encoding="utf-8") as output_file:
        output_file.write(
            text
            + "\n\n"
            + "Количество новых слов: "
            + str(len(filtered_excerpts[i][-4]))
            + "\nНовые слова: "
            + ", ".join(filtered_excerpts[i][-4])
            + "\nКоличество уникальных слов: "
            + str(len(filtered_excerpts[i][-3]))
            + "\nУникальные слова: "
            + ", ".join(filtered_excerpts[i][-3])
            + "\n"
            + "\nКласс: "
            + str(filtered_excerpts[i][-2])
            + "\nСекция: "
            + str(filtered_excerpts[i][-1])
            + "\n"
            + ("-" * 10)
            + "\n\n")
print(len(filtered_excerpts))