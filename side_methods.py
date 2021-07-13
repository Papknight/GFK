def reverse_data(old_file: str, new_file: str) -> None:
    with open(old_file, 'r') as f:
        data = f.readlines()

    new_data = []
    new_data.extend(data[0])
    new_data.extend(reversed(data[1:]))
    data = new_data

    with open(new_file, 'w') as nf:
        for record in data:
            nf.write(record)

    return None


if __name__ == '__main__':
    old_file = 'final/hitlist_data_january_reversed (CE, MDA, SDA, OE).csv'
    new_file = 'final/hitlist_data_january (CE, MDA, SDA, OE).csv'
    reverse_data(old_file, new_file)
