import mysql.connector
from collections import OrderedDict

HOST = 'localhost'
USER = 'root'
PASSWORD = ''
DB = 'LITESCALE'


class Dbconnect(object):
    # connession
    def __init__(self):
        self.dbconection = mysql.connector.connect(
            host=HOST, user=USER, password=PASSWORD, database=DB)
        self.dbcursor = self.dbconection.cursor(buffered=True)

    # close default
    def __del__(self):
        self.dbconection.close()

    # commit
    def commit(self):
        self.dbconection.commit()

    # close connection
    def close(self):
        self.dbcursor.close()
        self.dbconection.close()

    # insert
    def insert(self, table, ignore, *args, **kwargs):
        values = None
        if (ignore):
            query = "INSERT IGNORE INTO %s " % table
        else:
            query = "INSERT INTO %s " % table
        if kwargs:
            keys = kwargs.keys()
            values = tuple(kwargs.values())
            query += "(" + ",".join(["`%s`"] * len(keys)) % tuple(keys) + \
                ") VALUES (" + ",".join(["%s"]*len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"]*len(values)) + ")"

        try:
            self.dbcursor.execute(query, values)
            self.commit()
            return self.dbcursor.lastrowid
        except mysql.connector.Error as err:
            return err

    # delete
    def delete(self, table, where=None, *args):
        query = "DELETE FROM %s" % table
        if where:
            query += ' WHERE %s' % where

        values = tuple(args)

        try:
            self.dbcursor.execute(query, values)
            self.commit()
            return self.dbcursor.rowcount
        except mysql.connector.Error as err:
            return err

    # select
    def select(self, table, where=None, *args, **kwargs):
        result = None
        query = 'SELECT '
        keys = args
        values = tuple(kwargs.values())
        l = len(keys) - 1

        for i, key in enumerate(keys):
            query += "`"+key+"`"
            if i < l:
                query += ","

        query += 'FROM %s' % table

        if where:
            query += " WHERE %s" % where

        try:
            self.dbcursor.execute(query, values)
        except mysql.connector.Error as err:
            return err

        number_rows = self.dbcursor.rowcount
        number_columns = len(self.dbcursor.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self.dbcursor.fetchall()]
        else:
            result = [item[0] for item in self.dbcursor.fetchall()]

        return result

    # select advanced
    def select_advanced(self, sql, *args):
        od = OrderedDict(args)
        query = sql
        values = tuple(od.values())

        try:
            self.dbcursor.execute(query, values)
        except mysql.connector.Error as err:
            return err

        number_rows = self.dbcursor.rowcount
        number_columns = len(self.dbcursor.description)

        if number_rows >= 1 and number_columns > 1:
            result = [item for item in self.dbcursor.fetchall()]
        else:
            result = [item[0] for item in self.dbcursor.fetchall()]

        return result
