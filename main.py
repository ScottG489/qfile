#!/usr/bin/python2

import sys
import re
import sqlite3
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Parenthesis
# XXX: Validate SQL before trying to parse it otherwise unexpected behaviour will arise!
# TODO: Allow for file names with /'s in them.
# TODO: devise a method for automatically determining which regex to use. (file type/extension, fs location, some sort of `find` syntax, etc.)
# TODO: Add ability to get file names from statements containting JOINs.
# TODO: -s option for overriding default stdin regex valud in config.
# TODO: -c option to specify config file.
# TODO: Devise method for avoiding reserved keyword conflicts with filenames.
# TODO: Implement terser syntax without sql dependency for majority of use cases.
# TODO: Add functionality to write a table back to text (updates to the table would be reflected in the file)

# NOTE: Should eventually be ~/.qfilerc
#CONFIG_FILE = 'config'
CONFIG_FILE = '/home/scott/.qfilerc'

curs = sqlite3.connect(':memory:').cursor()

def main():
    query = sys.argv[1]
    filenames = get_filenames(query)

    if not sys.stdin.isatty():
        filenames.add('stdins')

    # Insert rows
    create_and_populate(filenames)

    run_query(query)

def get_entry_lists(match):
    gdict = match.groupdict()
    # Reverse lists. This seems to fix column ordering. Reliable?
    names = gdict.keys()[::-1]
    values = gdict.values()[::-1]

    return names, values

# TODO: Split this up into two functions (create/populate)
def create_and_populate(filenames):
    for filename in filenames:
        flist = file2list(filename)
        regex = get_var_from_file(filename + '.regex', CONFIG_FILE)

        match = get_first_match(flist, regex)

        if match:
            names, values = get_entry_lists(match)
            create_table(filename, names, values)
        else:
            raise Exception("No match found")

        for line in flist:
            match = re.search(regex, line)
            if match:
                names, values = get_entry_lists(match)
            else:
                continue
            insert_query = 'INSERT INTO ' + filename + ' values (' + ','.join('?' * len(values)) + ')'
            curs.execute(insert_query, values)

def get_first_match(flist, regex):
    for line in flist:
        match = re.search(regex, line)
        if match:
            return match
    return None


def run_query(query):
    for row in curs.execute(query):
        for i, col in enumerate(row):
            print str(col) + ('', '	|')[i != len(row) - 1],
        print

def is_find_token(token):
    return token.value.upper() == 'FROM'
def has_only_one_table(statement, index):
    return statement.token_next_by_instance(index, Identifier)

def get_table_names(statement, index):
    if has_only_one_table(statement, index):
        yield str(statement.token_next_by_instance(index, Identifier))
    else:
        identifier_list = statement.token_next_by_instance(index, IdentifierList)
        for ident in identifier_list.tokens:
            if isinstance(ident, Identifier):
                yield str(ident)

def get_subquery(token, index):
    return str(token.token_next_by_instance(index, Parenthesis))[1:-1]
# Finds the first occurance of a FROM statement then finds the next IdentifierList (which should be a list of the table names) and returns the values in the list.
def get_filenames(query):
    filenames = set()
    statement = sqlparse.parse(query)[0]
    for i, token in enumerate(statement.tokens):
        if is_find_token(token):
            for name in get_table_names(statement, i):
                filenames.add(name)
        elif isinstance(token, Where):
            for k, wtoken in enumerate(token.tokens):
                if isinstance(wtoken, Parenthesis):
                    filenames.update(get_filenames(get_subquery(token, k)))

    return filenames

                #return statement.token_next_by_instance(i, IdentifierList).value.replace(' ', '').split(',')

def create_table(filename, columns, first_row_data):
    create_query = 'CREATE TABLE ' + filename + ' ('
    for i, field in enumerate(columns):
        create_query += field + ' ' + ('text', 'numeric')[isnumber(first_row_data[i])] + ('', ', ')[i != len(columns) - 1]
    create_query += ')'
    curs.execute(create_query)

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
    if filename == 'stdins':
        flist = stdin2list()
    else:
        f = open(filename, 'r')
        flist = f.read().splitlines()
        f.close()

    return flist

def stdin2list():
    return sys.stdin.read().splitlines()

def isnumber(string):
    try:
        float(string)
        return True
    except:
        return False

if __name__ == "__main__":
    main()
