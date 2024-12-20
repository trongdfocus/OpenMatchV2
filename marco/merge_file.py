import pandas as pd

# Load the files
para = pd.read_csv("para.txt", sep="\t", header=None, names=["id", "text"])
para_title = pd.read_csv("para.title.txt", sep="\t", header=None, names=["id", "title"])

# Merge on the 'id' column
merged = pd.merge(para, para_title, on="id", how="left")

# Rearrange and sort
merged = merged[["id", "title", "text"]].sort_values(by="id")

# Save to output file
merged.to_csv("corpus.tsv", sep="\t", index=False, header=False)

input_file = "qidpidtriples.train.full.2.tsv"
output_file = "train.negatives.tsv"

with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    last_key = None
    line_parts = []

    for line in infile:
        # Split line into parts (tab-separated)
        parts = line.strip().split('\t')
        if len(parts) < 3:
            continue  # Skip lines with insufficient columns

        key, value = parts[0], parts[2]  # First column and third column

        # Check if current key matches the last key
        if key == last_key:
            # Append the third column to the existing line_parts
            line_parts.append(value)
        else:
            # Write the collected parts to the output file
            if last_key is not None:
                outfile.write(f"{last_key}\t{','.join(line_parts)}\n")
            # Start a new key
            last_key = key
            line_parts = [value]

    # Write the last collected group to the file
    if last_key is not None:
        outfile.write(f"{last_key}\t{','.join(line_parts)}\n")

print(f"Output written to {output_file}")
