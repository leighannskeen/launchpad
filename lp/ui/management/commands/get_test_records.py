"""
This command takes a full pass through the database looking for MARC records
that match the fields we extract. If records are found they are saved to
the testdata directory.
"""

import os
import logging

from django.db import connection
from django.core.management.base import BaseCommand

from ui import marc
from ui.voyager import get_marc_blob


# where to write the records
test_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'data')

# keep track of what field specifications have got marc records
field_specs_found = set()

# the total number of field specifications, so we know when we're done
num_field_specs = 0
for name, display_name, specs in marc.mapping:
    for spec in specs:
        num_field_specs += 1


class Command(BaseCommand):
    help = 'extract marc records from voyager for testing'

    def handle(self, *args, **kwargs):

        for bib_id, record in records():
            # no need to continue if we have found everything
            if num_field_specs == len(field_specs_found):
                logging.info("found marc records for all field specifications")
                break

            # provide an indicator of records being looked at
            logging.info("examining %s", bib_id)

            for name, display_name, field_specs in marc.mapping:
                for fs in field_specs:
                    if not fs in field_specs_found:
                        found = check_record(bib_id, record, name, fs)
                        if found:
                            field_specs_found.add(fs)

        # report any field specs that we couldn't find a record fo
        for fs in field_specs:
            if fs not in field_specs_found:
                logging.info("unable to find field spec: %s", fs)


def check_record(bib_id, record, name, field_spec, overwrite=False):
    # determine where the marc record would be saved if there is a match
    # if we already have a file and we're not overwriting we can return
    # immediately
    filename = os.path.join(test_data_dir, "%s.mrc" % field_spec)
    if os.path.isfile(filename) and not overwrite:
        return True

    found = False

    # most field specifications are just a tag name
    if type(field_spec) == str:
        fields = record.get_fields(field_spec)
        if len(fields) > 0:
            found = True

    # otherwise we need to unpack the field specification and check that
    # all the conditions are met
    else:
        tag, ind1, ind2, subfields = field_spec
        for field in record.get_fields(tag):
            logging.info("looking at %s" % field)
            if marc.ind(ind1, field.indicator1) and \
                    marc.ind(ind2, field.indicator2):
                found = True

    if found:
        try:
            open(filename, "wb").write(record.as_marc())
            logging.info("found: %s %s", name, field_spec)
        except Exception as e:
            logging.warn("unable to serialize %s: %s", bib_id, e)

    return found


def records():
    cursor = connection.cursor()
    query = """
            SELECT BIB_ID
            FROM bib_master
            WHERE SUPPRESS_IN_OPAC = 'N'
            ORDER BY BIB_ID DESC
            """
    cursor.execute(query)
    while True:
        try:
            row = cursor.fetchone()
            if not row:
                break
            bib_id = row[0]
            record = get_marc_blob(bib_id)
            yield bib_id, record
        except Exception as e:
            logging.warn("exception when getting marc for %s: %s", bib_id, e)
