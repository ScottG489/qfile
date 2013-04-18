#!/usr/bin/python2

import sys
import re
import sqlite3
# TODO: -c option to specify config file.
# TODO: devise a method for automatically determining config file to use. (file type/extension, fs location, etc.)
# TODO: Implement terser syntax without sql dependency for majority of use cases.
# TODO: Multi-file/table support.

def main():
    query = sys.argv[1]
    regex = get_var_from_file('regex', 'config')
    filename = re.search(r'from (\w+)', query).group(1)
    flist = file2list(filename)

    curs = sqlite3.connect(':memory:').cursor()

    # Insert rows
    table_exists = False
    for line in flist:
        values = []
        match = re.search(regex, line)
        if match:
            gdict = match.groupdict()
            # Reverse lists. This seems to fix column ordering. Reliable?
            names = gdict.keys()[::-1]
            values = gdict.values()[::-1]
            if not table_exists:
                create_table(curs, filename, names)
                table_exists = True
        else:
            continue
        insert_query = 'INSERT INTO ' + filename + ' values (' + ','.join('?' * len(values)) + ')'
        curs.execute(insert_query, values)

    for row in curs.execute(query):
        for col in row:
            print col + ',',
        print

def create_table(cursor, filename, columns):
    create_query = 'CREATE TABLE ' + filename + ' ('
    for i, field in enumerate(columns):
        create_query += field + ' text' + ('', ', ')[i != len(columns) - 1]
    create_query += ')'
    cursor.execute(create_query)

def get_var_from_file(var_name, filename):
    read_file = open(filename, 'r')
    file_str = read_file.read()
    read_file.close()

    return re.search(var_name + '=(.*)', file_str).group(1)

# Reads file into list delimited by newlines (strips newlines)
def file2list(filename):
    f = open(filename, 'r')
    flist = f.read().splitlines()
    f.close()

    return flist

if __name__ == "__main__":
    main()
