# https://github.com/GoogleCloudPlatform/cloud-sql-python-connector

from google.cloud.sql.connector import Connector
import sqlalchemy
import pymysql
import os
from google.cloud import storage
import csv
from typing import List, Dict, Optional
import pandas as pd

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bsid-user-group5-sa-key.json"
storage_client = storage.Client()

# initialize Connector object
connector = Connector()


# function to return the database connection
def getconn() -> pymysql.connections.Connection:
    conn: pymysql.connections.Connection = connector.connect(
        "tsmchack2023-bsid-grp5:asia-east1:tsmchack2023-bsid-mysql-db",
        "pymysql",
        user="root",
        password="DRScS43g",
        db="mysql",
    )
    return conn


# create connection pool
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)


# query entry_records table
def query_entry_records():
    r = []
    with pool.connect() as db_conn:
        result = db_conn.execute("SELECT * from parking.entry_records").fetchall()

        # Do something with the results
        for row in result:
            r.append(
                {
                    "license_plate": row[0],
                    "entry_time": row[1],
                    "exit_time": row[2],
                    "parking_number": row[3],
                }
            )
    return r


# query reservation table
def query_reservation():
    r = []
    with pool.connect() as db_conn:
        result = db_conn.execute("SELECT * from parking.reservation").fetchall()

        # Do something with the results
        for row in result:
            r.append(
                {
                    "license_plate": row[0],
                    "eff_start_time": row[1],
                    "eff_end_time": row[2],
                    "parking_number": row[3],
                }
            )
    return r


# query blacklist table
def query_blacklist():
    r = []
    with pool.connect() as db_conn:
        result = db_conn.execute("SELECT * from parking.blacklist").fetchall()

        # Do something with the results
        for row in result:
            r.append(
                {
                    "license_plate": row[0],
                    "block_start_time": row[1],
                    "block_end_time": row[2],
                }
            )
    return r


# query parking_space table
def query_parking_space():
    r = []
    with pool.connect() as db_conn:
        result = db_conn.execute("SELECT * from parking.parking_space").fetchall()

        # Do something with the results
        for row in result:
            r.append(
                {
                    "parking_number": row[0],
                    "is_available": row[1],
                    "license_plate": row[2],
                }
            )
    return r


# query user table
def query_user():
    r = []
    with pool.connect() as db_conn:
        result = db_conn.execute("SELECT * from parking.user").fetchall()

        # Do something with the results
        for row in result:
            r.append(
                {
                    "account": row[0],
                    "password": row[1],
                    "manager": row[2],
                }
            )
    return r


# insert into entry_records table
def insert_entry_records(license_plate, entry_time, exit_time, parking_number):
    # insert statement
    insert_stmt = sqlalchemy.text(
        "INSERT INTO parking.entry_records (license_plate, entry_time, exit_time, parking_number) "
        + "VALUES (:license_plate, :entry_time, :exit_time, :parking_number)"
    )

    with pool.connect() as db_conn:
        db_conn.execute(
            insert_stmt,
            license_plate=license_plate,
            entry_time=entry_time,
            exit_time=exit_time,
            parking_number=parking_number,
        )
    return {"insert": "success"}


# insert into reservation table
def insert_reservation(license_plate, eff_start_time, eff_end_time, parking_number):
    # insert statement
    insert_stmt = sqlalchemy.text(
        "INSERT INTO parking.reservation (license_plate, eff_start_time, eff_end_time, parking_number) "
        + "VALUES (:license_plate, :eff_start_time, :eff_end_time, :parking_number)"
    )

    with pool.connect() as db_conn:
        db_conn.execute(
            insert_stmt,
            license_plate=license_plate,
            eff_start_time=eff_start_time,
            eff_end_time=eff_end_time,
            parking_number=parking_number,
        )
    return {"insert": "success"}


# insert into blacklist table
def insert_blacklist(license_plate, block_start_time, block_end_time):
    # insert statement
    insert_stmt = sqlalchemy.text(
        "INSERT INTO parking.blacklist (license_plate, block_start_time, block_end_time) "
        + "VALUES (:license_plate, :block_start_time, :block_end_time)"
    )

    with pool.connect() as db_conn:
        db_conn.execute(
            insert_stmt,
            license_plate=license_plate,
            block_start_time=block_start_time,
            block_end_time=block_end_time,
        )
    return {"insert": "success"}


# insert into user table
def insert_user(account, password, manager):
    # insert statement
    insert_stmt = sqlalchemy.text(
        "INSERT INTO parking.user (account, password, manager) "
        + "VALUES (:account, :password, :manager)"
    )

    with pool.connect() as db_conn:
        db_conn.execute(
            insert_stmt, account=account, password=password, manager=manager
        )
    return {"insert": "success"}


def reset_entry_records():
    # Create table
    with pool.connect() as db_conn:
        db_conn.execute("drop table parking.entry_records")
        db_conn.execute(
            "CREATE TABLE parking.entry_records(license_plate VARCHAR(50), entry_time TIME, exit_time TIME, parking_number VARCHAR(50));"
        )

    # Read entry_records and public_scenario_data_groundtruth
    entry_records_df = pd.read_csv(
        "/root/adslXmlad/read_bucket/tsmchack2023-bsid-grp5-public-read-bucket/reference_data/entry_records.csv"
    )
    public_scenario_data_groundtruth_df = pd.read_csv(
        "/root/adslXmlad/read_bucket/tsmchack2023-bsid-grp5-public-read-bucket/reference_data/public_scenario_data_groundtruth.csv"
    )
    for i, row in entry_records_df.iterrows():
        if (
            len(
                public_scenario_data_groundtruth_df[
                    public_scenario_data_groundtruth_df["license_plate"]
                    == row["license_plate"]
                ]
            )
            == 0
        ):
            # We don't have any image for this license plate
            continue
        if int(row["entry_time"][:2]) >= 16:
            # We don't need to store the entry records after 16:00
            continue
        if int(row["entry_time"][:2]) <= 16 and int(row["exit_time"][:2]) >= 16:
            exit_time = "00:23:59"
        else:
            exit_time = "00:" + row["exit_time"]

        parking_number = (
            public_scenario_data_groundtruth_df[
                public_scenario_data_groundtruth_df["license_plate"]
                == row["license_plate"]
            ]["output_filename"]
            .iloc[0]
            .split("_")[0]
        )
        insert_entry_records(
            row["license_plate"],
            "00:" + row["entry_time"],
            exit_time,
            parking_number,
        )
    return {"reset": "success"}


def reset_reservation():
    with pool.connect() as db_conn:
        db_conn.execute("drop table parking.reservation")
        db_conn.execute(
            "CREATE TABLE parking.reservation(license_plate VARCHAR(50),eff_start_time TIME, eff_end_time TIME, parking_number VARCHAR(50));"
        )
    with open(
        "/root/adslXmlad/read_bucket/tsmchack2023-bsid-grp5-public-read-bucket/reference_data/reservation.csv",
        newline="",
    ) as csvfile:
        rows = csv.DictReader(csvfile)
        for row in rows:
            insert_reservation(
                row["license_plate"],
                "00:" + row["eff_start_time"],
                "00:" + row["eff_end_time"],
                row["parking_number"],
            )
    return {"reset": "success"}


def reset_blacklist():
    with pool.connect() as db_conn:
        db_conn.execute("drop table parking.blacklist")
        db_conn.execute(
            "CREATE TABLE parking.blacklist(license_plate VARCHAR(50),block_start_time TIME, block_end_time TIME);"
        )
    with open(
        "/root/adslXmlad/read_bucket/tsmchack2023-bsid-grp5-public-read-bucket/reference_data/blacklist.csv",
        newline="",
    ) as csvfile:
        rows = csv.DictReader(csvfile)
        for row in rows:
            insert_blacklist(
                row["license_plate"],
                "00:" + row["block_start_time"],
                "00:" + row["block_end_time"],
            )
    return {"reset": "success"}


# delete entry_records table
def delete_entry_records(license_plate, entry_time, exit_time, parking_number):
    delete_stmt = sqlalchemy.text(
        "DELETE FROM parking.entry_records WHERE license_plate=:license_plate AND entry_time=:entry_time AND exit_time=:exit_time AND parking_number=:parking_number"
    )

    with pool.connect() as db_conn:
        db_conn.execute(
            delete_stmt,
            license_plate=license_plate,
            entry_time=entry_time,
            exit_time=exit_time,
            parking_number=parking_number,
        )


# delete reservation table
def delete_reservation(license_plate, eff_start_time, eff_end_time, parking_number):
    delete_stmt = sqlalchemy.text(
        "DELETE FROM parking.reservation WHERE license_plate=:license_plate AND eff_start_time=:eff_start_time AND eff_end_time=:eff_end_time AND parking_number=:parking_number"
    )

    with pool.connect() as db_conn:
        db_conn.execute(
            delete_stmt,
            license_plate=license_plate,
            eff_start_time=eff_start_time,
            eff_end_time=eff_end_time,
            parking_number=parking_number,
        )


# delete blacklist table
def delete_blacklist(license_plate, block_start_time, block_end_time):
    delete_stmt = sqlalchemy.text(
        "DELETE FROM parking.blacklist WHERE license_plate=:license_plate AND block_start_time=:block_start_time AND block_end_time=:block_end_time"
    )

    with pool.connect() as db_conn:
        db_conn.execute(
            delete_stmt,
            license_plate=license_plate,
            block_start_time=block_start_time,
            block_end_time=block_end_time,
        )


def access_table(mode: str, table: str, data: Optional[Dict] = None):
    if mode == "query":
        if table == "entry_records":
            return query_entry_records()
        elif table == "reservation":
            return query_reservation()
        elif table == "blacklist":
            return query_blacklist()
        elif table == "parking_space":
            return query_parking_space()
        elif table == "user":
            return query_user()
        else:
            return "Error: table not found"
    elif mode == "insert":
        if table == "entry_records":
            return insert_entry_records(**data)
        elif table == "reservation":
            return insert_reservation(**data)
        elif table == "blacklist":
            return insert_blacklist(**data)
        elif table == "user":
            return insert_user(**data)
        else:
            return "Error: table not found"
    elif mode == "reset":
        if table == "entry_records":
            return reset_entry_records()
        elif table == "reservation":
            return reset_reservation()
        elif table == "blacklist":
            return reset_blacklist()
        else:
            return "Error: table not found"
    elif mode == "delete":
        if table == "entry_records":
            return delete_entry_records(**data)
        elif table == "reservation":
            return delete_reservation(**data)
        elif table == "blacklist":
            return delete_blacklist(**data)
        else:
            return "Error: table not found"
