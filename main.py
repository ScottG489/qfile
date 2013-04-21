#!/usr/bin/python2

import sys
import re
import sqlite3
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
# TODO: -c option to specify config file.
# TODO: devise a method for automatically determining config file to use. (file type/extension, fs location, etc.)
# TODO: Implement terser syntax without sql dependency for majority of use cases.
# TODO: Multi-file/table support.
# TODO: Add functionality to write a table back to text (updates to the table would be reflected in the file)

def main():
    query = sys.argv[1]
    filenames = get_filenames(query)

    curs = sqlite3.connect(':memory:').cursor()

    # Insert rows
    for filename in filenames:
        flist = file2list(filename)
        table_exists = False
        regex = get_var_from_file(filename + '.regex', 'config')
        for line in flist:
            values = []
            match = re.search(regex, line)
            if match:
                gdict = match.groupdict()
                # Reverse lists. This seems to fix column ordering. Reliable?
                names = gdict.keys()[::-1]
                values = gdict.values()[::-1]
                if not table_exists:
                    create_table(curs, filename, names, values)
                    table_exists = True
            else:
                continue
            insert_query = 'INSERT INTO ' + filename + ' values (' + ','.join('?' * len(values)) + ')'
            curs.execute(insert_query, values)

    for row in curs.execute(query):
        for i, col in enumerate(row):
            print str(col) + ('', '	|')[i != len(row) - 1],
        print

# Finds the first occurance of a FROM statement then finds the next IdentifierList (which should be a list of the table names) and returns the values in the list.
def get_filenames(query):
    statement = sqlparse.parse(query)[0]
    for i, token in enumerate(statement.tokens):
        if token.value.upper() == 'FROM':
            table_name = statement.token_next_by_instance(i, Identifier)
            if table_name:
                return [table_name.value]
            else:
                return statement.token_next_by_instance(i, IdentifierList).value.replace(' ', '').split(',')

def create_table(cursor, filename, columns, first_row_data):
    create_query = 'CREATE TABLE ' + filename + ' ('
    for i, field in enumerate(columns):
        create_query += field + ' ' + ('text', 'numeric')[isnumber(first_row_data[i])] + ('', ', ')[i != len(columns) - 1]
    create_query += ')'
    cursor.execute(create_query)

def get_var_from_file(var_name, filename):
    file_str = file2str(filename)

    return re.search(var_name + '=(.*)', file_str).group(1)

def file2str(filename):
    read_file = open(filename, 'r')
    file_str = read_file.read()
    read_file.close()

    return file_str

# Reads file into list delimited by newlines (strips newlines)
def file2list(filename):
    f = open(filename, 'r')
    flist = f.read().splitlines()
    f.close()

    return flist

def isnumber(string):
    try:
        float(string)
        return True
    except:
        return False

if __name__ == "__main__":
    main()
