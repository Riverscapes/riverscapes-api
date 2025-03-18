"""
Dumps Riverscapes Data Exchange projects to a SQLite database
"""
import os
from datetime import datetime, timezone
from rsxml import Logger
from rsapi import RiverscapesAPI, RiverscapesSearchParams
from rsapi.imports import import_sqlite3

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'riverscapes_schema.sql')

sqlite3 = import_sqlite3()


def dump_riverscapes(rs_api: RiverscapesAPI, db_path: str, search_tags: str = None) -> None:
    """ DUmp all projects to a DB

    Args:
        output_folder ([type]): [description]
    """
    log = Logger('DUMP Riverscapes to SQlite')
    log.title('Dump Riverscapes to SQLITE')

    # We can run this multiple times without any worry
    create_database(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    curs = conn.cursor()

    # Basically just search for everything
    searchParams = RiverscapesSearchParams({
        'tags': [tag.strip() for tag in search_tags.split(',')],
    })

    # Determine last created date projects in the database.
    # Delete all projects that were in that same day and then start the download
    # for that day over again. This will ensure we don't have duplicates.
    curs.execute("SELECT MAX(created_on) FROM rs_projects")
    last_inserted_row = curs.fetchone()

    # NOTE: Big caveat here. The search is reverse chronological so this will only work if you've already allowed it
    # to fully complete once.
    if last_inserted_row[0] is not None:
        # Convert milliseconds to seconds and create a datetime object
        last_inserted = datetime.fromtimestamp(last_inserted_row[0] / 1000, tz=timezone.utc)
        searchParams.createdOnFrom = last_inserted

    # Create a timedelta object with a difference of 1 day
    for project, _stats, _searchtotal, _prg in rs_api.search(searchParams, progress_bar=True, page_size=100):

        # Attempt to retrieve the huc10 from the project metadata if it exists
        huc10 = None
        for key in ['HUC10', 'huc10', 'HUC', 'huc']:
            if key in project.project_meta:
                value = project.project_meta[key]
                huc10 = value
                break

        # Attempt to retrieve the model version from the project metadata if it exists
        model_version = None
        for key in ['model_version', 'modelVersion', 'Model Version']:
            if key in project.project_meta:
                model_version = project.project_meta[key]
                break

        # Insert project data
        curs.execute('''
            INSERT INTO rs_projects(project_id, name, tags, huc10, model_version, project_type_id, created_on, owned_by_id, owned_by_name, owned_by_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING
            ''',
                     (
                         project.id,
                         project.name,
                         ','.join(project.tags),
                         huc10,
                         model_version,
                         project.project_type,
                         int(project.created_date.timestamp() * 1000),
                         project.json['ownedBy']['id'],
                         project.json['ownedBy']['name'],
                         project.json['ownedBy']['__typename']
                     ))

        # Don't rely on curs.lastrowid because it's not reliable when using ON CONFLICT DO NOTHING
        curs.execute('SELECT id FROM rs_projects WHERE project_id = ?', [project.id])
        project_id = curs.fetchone()[0]

        # Insert project meta data
        curs.executemany('INSERT INTO rs_project_meta (project_id, key, value) VALUES (?, ?, ?) ON CONFLICT DO NOTHING', [
            (project_id, key, value) for key, value in project.project_meta.items()
        ])

    conn.commit()
    log.info(f'Finished Writing: {db_path}')


def create_database(db_path: str):
    """ Incorporate the Riverscapes Data Exchange schema into the SQLite database
    """
    log = Logger('Create Database')

    if not os.path.exists(SCHEMA_FILE):
        raise Exception(f'The schema file does not exist: {SCHEMA_FILE}')

    # Read the schema from the file
    with open(SCHEMA_FILE, 'r', encoding='utf8') as file:
        schema = file.read()

    # Connect to a new (or existing) database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute the schema to create tables
    log.info(f'Creating RIVERSCAPES database tables (if not exist): {db_path}')
    cursor.executescript(schema)

    conn.commit()
    conn.close()
